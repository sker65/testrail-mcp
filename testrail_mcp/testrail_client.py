"""TestRail API client module."""
import base64
import json
import time
import random
from typing import Dict, List, Any, Optional, Union, Tuple
import requests

# (connect timeout, read timeout) in seconds. TestRail bulk queries on large
# projects can be slow, so the read timeout is generous while the connect
# timeout stays short to fail fast on unreachable hosts.
DEFAULT_TIMEOUT: Tuple[float, float] = (10.0, 60.0)

# HTTP status codes worth retrying (rate limiting + transient server errors).
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 1.0  # seconds; exponential: base * 2**attempt (+ jitter)


class TestRailClient:
    """TestRail API client for interacting with TestRail."""

    def __init__(self, base_url: str, username: str, api_key: str,
                 timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 backoff_base: float = DEFAULT_BACKOFF_BASE):
        """
        Initialize the TestRail API client.
        
        Args:
            base_url: The URL of your TestRail instance (e.g., [https://example.testrail.io/)](https://example.testrail.io/))
            username: Your TestRail username/email
            api_key: Your TestRail API key
            timeout: (connect, read) timeout in seconds for every HTTP request
            max_retries: Number of retries for transient failures (429/5xx/network)
            backoff_base: Base seconds for exponential backoff between retries
        """
        self.username = username
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        
        # Ensure the base URL ends with a slash
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url + 'index.php?/api/v2/'
        
        # Set up the session with authentication
        self.session = requests.Session()
        auth = str(
            base64.b64encode(
                bytes(f'{username}:{api_key}', 'utf-8')
            ),
            'ascii'
        ).strip()
        self.session.headers.update({
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json',
        })

    def _sleep_backoff(self, attempt: int, retry_after: Optional[str] = None) -> None:
        """Sleep before a retry using Retry-After (if present) or exponential backoff."""
        if retry_after:
            try:
                time.sleep(min(float(retry_after), 60.0))
                return
            except (TypeError, ValueError):
                pass
        delay = self.backoff_base * (2 ** attempt)
        # Full jitter to avoid thundering-herd retries across concurrent calls.
        time.sleep(min(delay + random.uniform(0, self.backoff_base), 60.0))

    def _execute(self, method: str, url: str, data: Optional[Dict] = None) -> requests.Response:
        """
        Perform a single HTTP request with a timeout, retrying transient failures.

        Retries on network errors (connect/read timeouts, connection drops) and on
        429/5xx responses, using Retry-After or exponential backoff. Non-retryable
        HTTP errors (e.g. 4xx) are returned to the caller for error extraction.
        """
        method = method.upper()
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if method == 'GET':
                    response = self.session.get(url, timeout=self.timeout)
                elif method == 'POST':
                    response = self.session.post(
                        url, data=json.dumps(data) if data else None, timeout=self.timeout)
                elif method == 'PUT':
                    response = self.session.put(
                        url, data=json.dumps(data) if data else None, timeout=self.timeout)
                elif method == 'DELETE':
                    response = self.session.delete(url, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
            except (requests.Timeout, requests.ConnectionError) as exc:
                # Transient network problem: retry with backoff, then re-raise.
                last_exc = exc
                if attempt < self.max_retries:
                    self._sleep_backoff(attempt)
                    continue
                raise Exception(
                    f"TestRail request to {url} failed after "
                    f"{self.max_retries + 1} attempts: {exc}"
                ) from exc

            if response.status_code in RETRYABLE_STATUS and attempt < self.max_retries:
                self._sleep_backoff(attempt, response.headers.get('Retry-After'))
                continue

            return response

        # Unreachable in practice, but keeps type-checkers happy.
        raise Exception(f"TestRail request to {url} failed: {last_exc}")

    def _send_request(self, method: str, uri: str, data: Optional[Dict] = None) -> Any:
        """
        Send a request to the TestRail API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            uri: API endpoint URI
            data: Request data for POST/PUT requests
            
        Returns:
            Response data from TestRail
            
        Raises:
            Exception: If the request fails
        """
        url = self.base_url + uri
        response = self._execute(method, url, data)

        if response.status_code >= 300:
            try:
                error = response.json()
            except:
                error = response.text
            raise Exception(f"TestRail API returned HTTP {response.status_code}: {error}")
            
        return response.json() if response.content else {}

    def _send_request_raw(self, method: str, uri: str) -> requests.Response:
        """
        Send a request and return the raw response (for binary downloads).

        Args:
            method: HTTP method (GET)
            uri: API endpoint URI

        Returns:
            Raw requests.Response object

        Raises:
            Exception: If the request fails
        """
        url = self.base_url + uri
        response = self._execute(method, url)

        if response.status_code >= 300:
            try:
                error = response.json()
            except:
                error = response.text
            raise Exception(f"TestRail API returned HTTP {response.status_code}: {error}")

        return response

    @staticmethod
    def _extract_next_uri(next_link: str) -> Optional[str]:
        """
        Turn a TestRail `_links.next` value into a base_url-relative URI.

        `base_url` already ends with `index.php?/api/v2/`, so the leading `/api/v2/` from
        the next link must be stripped before appending. If the `api/v2/` marker is absent
        (clean-URL installs / proxy path rewrites), the link is un-parseable in this context;
        return None to STOP rather than build a malformed URL and loop on a bad page.
        """
        marker = 'api/v2/'
        idx = next_link.lower().find(marker)
        if idx == -1:
            return None
        return next_link[idx + len(marker):].lstrip('/')

    def _get_paginated(self, uri: str, entity_key: str, max_pages: int = 1000,
                       start_offset: int = 0, page_size: int = 250,
                       id_key: Optional[str] = 'id') -> Dict:
        """
        Fetch pages of a paginated TestRail bulk-API GET endpoint.

        Handles both response shapes:
          * bulk API (recent TestRail): {offset, limit, size, _links:{next}, <entity_key>:[...]}
          * legacy bare list:           [ ... ]

        Args:
            uri: endpoint URI (may already contain query params joined with '&')
            entity_key: response key holding the list (e.g. 'cases', 'tests')
            max_pages: max pages to fetch in THIS call. Bound it to keep a single
                MCP call under the client's request deadline. When more data
                remains, `next_offset`/`is_last` in the result let the caller resume.
            start_offset: offset to begin at (for resumable/cursor paging)
            page_size: rows per page (TestRail max is 250)
            id_key: field used to de-duplicate rows across pages/resumes. Offset
                paging can repeat rows if cases are edited mid-scan; de-dup makes
                the merged result safe. Set None to disable.

        Returns a normalized dict:
            {
              entity_key: [items...],   # items fetched in THIS call
              "size": <int>,            # len of items in THIS call
              "offset": <start_offset>,
              "next_offset": <int|None>, # pass back as offset= to continue; None if done
              "is_last": <bool>,         # True when no more pages remain
              "pages_fetched": <int>
            }
        """
        items: List[Dict] = []
        seen_ids: set = set()
        page_size = max(1, min(int(page_size), 250))
        offset = max(0, int(start_offset))

        # Build the first page URI with explicit limit/offset so behaviour is
        # deterministic across TestRail versions and offset arithmetic is predictable.
        next_uri: Optional[str] = f'{uri}&limit={page_size}&offset={offset}'
        prev_uri: Optional[str] = None
        pages = 0
        more_remaining = False
        last_offset = offset

        def _add(rows: List[Dict]) -> None:
            for row in rows or []:
                if id_key is not None and isinstance(row, dict) and id_key in row:
                    rid = row[id_key]
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                items.append(row)

        while next_uri and pages < max_pages:
            # Offset-monotonicity guard: if the derived next link does not advance, stop
            # after one extra request instead of hammering the same page repeatedly.
            if next_uri == prev_uri:
                break
            pages += 1
            resp = self._send_request('GET', next_uri)
            prev_uri = next_uri
            last_offset = offset

            # Legacy TestRail returned a bare list (no pagination envelope). An empty
            # response (`{}`) yields items=[] with no `_links` and ends cleanly below.
            if isinstance(resp, list):
                _add(resp)
                break
            if not isinstance(resp, dict):
                break

            _add(resp.get(entity_key, []))

            nxt = (resp.get('_links') or {}).get('next')
            if not nxt:
                break

            next_uri = self._extract_next_uri(nxt)
            offset += page_size

            # Hit this call's page budget but more data exists -> signal resume.
            if next_uri and pages >= max_pages:
                more_remaining = True
                break

        result = {
            entity_key: items,
            "size": len(items),
            "offset": last_offset if pages else start_offset,
            "next_offset": offset if more_remaining else None,
            "is_last": not more_remaining,
            "pages_fetched": pages,
        }
        return result

    # Cases API
    def get_case(self, case_id: int) -> Dict:
        """Get a test case by ID."""
        return self._send_request('GET', f'get_case/{case_id}')
    
    def get_cases(self, project_id: int, suite_id: Optional[int] = None,
                  section_id: Optional[int] = None,
                  created_after: Optional[int] = None,
                  updated_after: Optional[int] = None,
                  filter: Optional[str] = None,
                  offset: int = 0, limit: int = 250,
                  max_pages_per_call: int = 1000) -> Dict:
        """
        Get test cases for a project/suite with resumable cursor paging.

        With defaults it auto-paginates the whole project (backward compatible).
        For large projects, set `max_pages_per_call` (and use the returned
        `next_offset`) to fetch in bounded, deadline-safe batches.

        Returns dict with: cases, size, offset, next_offset, is_last, pages_fetched.
        """
        uri = f'get_cases/{project_id}'
        if suite_id:
            uri += f'&suite_id={suite_id}'
        if section_id:
            uri += f'&section_id={section_id}'
        if created_after:
            uri += f'&created_after={created_after}'
        if updated_after:
            uri += f'&updated_after={updated_after}'
        if filter:
            uri += f'&filter={filter}'
        return self._get_paginated(
            uri, 'cases', max_pages=max_pages_per_call,
            start_offset=offset, page_size=limit, id_key='id')
    
    def add_case(self, section_id: int, data: Dict) -> Dict:
        """Add a new test case."""
        return self._send_request('POST', f'add_case/{section_id}', data)
    
    def update_case(self, case_id: int, data: Dict) -> Dict:
        """Update an existing test case."""
        return self._send_request('POST', f'update_case/{case_id}', data)
    
    def delete_case(self, case_id: int) -> Dict:
        """Delete a test case."""
        return self._send_request('POST', f'delete_case/{case_id}')
    
    # Projects API
    def get_project(self, project_id: int) -> Dict:
        """Get a project by ID."""
        return self._send_request('GET', f'get_project/{project_id}')
    
    def get_projects(self) -> Dict:
        """Get ALL projects (auto-paginated)."""
        return self._get_paginated('get_projects', 'projects')
    
    def add_project(self, data: Dict) -> Dict:
        """Add a new project."""
        return self._send_request('POST', 'add_project', data)
    
    def update_project(self, project_id: int, data: Dict) -> Dict:
        """Update an existing project."""
        return self._send_request('POST', f'update_project/{project_id}', data)
    
    def delete_project(self, project_id: int) -> Dict:
        """Delete a project."""
        return self._send_request('POST', f'delete_project/{project_id}')
    
    # Runs API
    def get_run(self, run_id: int) -> Dict:
        """Get a test run by ID."""
        return self._send_request('GET', f'get_run/{run_id}')
    
    def get_runs(self, project_id: int) -> List[Dict]:
        """Get all test runs for a project."""
        return self._send_request('GET', f'get_runs/{project_id}')
    
    def add_run(self, project_id: int, data: Dict) -> Dict:
        """Add a new test run."""
        return self._send_request('POST', f'add_run/{project_id}', data)
    
    def update_run(self, run_id: int, data: Dict) -> Dict:
        """Update an existing test run."""
        return self._send_request('POST', f'update_run/{run_id}', data)
    
    def close_run(self, run_id: int) -> Dict:
        """Close a test run."""
        return self._send_request('POST', f'close_run/{run_id}')
    
    def delete_run(self, run_id: int) -> Dict:
        """Delete a test run."""
        return self._send_request('POST', f'delete_run/{run_id}')
    
    # Tests API
    def get_tests(self, run_id: int, offset: int = 0, limit: int = 250,
                  max_pages_per_call: int = 1000) -> Dict:
        """
        Get tests for a run with resumable cursor paging.

        Returns dict with: tests, size, offset, next_offset, is_last, pages_fetched.
        """
        return self._get_paginated(
            f'get_tests/{run_id}', 'tests', max_pages=max_pages_per_call,
            start_offset=offset, page_size=limit, id_key='id')

    # Results API
    def get_results(self, test_id: int, offset: int = 0, limit: int = 250,
                    max_pages_per_call: int = 1000) -> Dict:
        """
        Get results for a test with resumable cursor paging.

        Returns dict with: results, size, offset, next_offset, is_last, pages_fetched.
        """
        return self._get_paginated(
            f'get_results/{test_id}', 'results', max_pages=max_pages_per_call,
            start_offset=offset, page_size=limit, id_key='id')
    
    def get_results_for_run(self, run_id: int) -> List[Dict]:
        """Get all results for a run."""
        return self._send_request('GET', f'get_results_for_run/{run_id}')
    
    def add_result(self, test_id: int, data: Dict) -> Dict:
        """Add a new result for a test."""
        return self._send_request('POST', f'add_result/{test_id}', data)
    
    def add_results(self, run_id: int, data: Dict) -> List[Dict]:
        """Add multiple results for a run."""
        return self._send_request('POST', f'add_results/{run_id}', data)
    
    def add_results_for_cases(self, run_id: int, data: Dict) -> List[Dict]:
        """Add results for specific cases in a run."""
        return self._send_request('POST', f'add_results_for_cases/{run_id}', data)
    
    # Datasets API (assuming TestRail has dataset endpoints)
    def get_datasets(self, project_id: int) -> List[Dict]:
        """Get all datasets for a project."""
        return self._send_request('GET', f'get_datasets/{project_id}')
    
    def get_dataset(self, dataset_id: int) -> Dict:
        """Get a dataset by ID."""
        return self._send_request('GET', f'get_dataset/{dataset_id}')
    
    def add_dataset(self, project_id: int, data: Dict) -> Dict:
        """Add a new dataset."""
        return self._send_request('POST', f'add_dataset/{project_id}', data)
    
    def update_dataset(self, dataset_id: int, data: Dict) -> Dict:
        """Update an existing dataset."""
        return self._send_request('POST', f'update_dataset/{dataset_id}', data)
    
    def delete_dataset(self, dataset_id: int) -> Dict:
        """Delete a dataset."""
        return self._send_request('POST', f'delete_dataset/{dataset_id}')

    # Sections API
    def get_section(self, section_id:int) -> Dict:
        """Get a specific section"""
        return self._send_request('GET', f'get_section/{section_id}')

    def get_sections(self, project_id: int, suite_id: Optional[int] = None) -> Dict:
        """Get ALL sections for a project/suite (auto-paginated)."""
        uri = f'get_sections/{project_id}'
        if suite_id:
            uri += f'&suite_id={suite_id}'
        return self._get_paginated(uri, 'sections')

    def add_section(self, project_id:int, data:Dict) -> Dict:
        """Add a new section"""
        return self._send_request('POST', f'add_section/{project_id}', data)

    def update_section(self, section_id:int, data:Dict) -> Dict:
        """Update an existing section"""
        return self._send_request('POST', f'update_section/{section_id}', data)

    def delete_section(self, section_id:int, soft:bool) -> Dict:
        """Delete an existing section"""
        url = f'delete_section/{section_id}'
        if (soft):
            url = f'delete_section/{section_id}?soft=1'
        return self._send_request('POST', url)

    def move_section(self, section_id:int, data: Dict) -> Dict:
        """Move a section to a different parent or position"""
        return self._send_request('POST', f'move_section/{section_id}', data)

    # Attachments API
    def get_attachments_for_case(self, case_id: int, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict:
        """Get all attachments for a test case."""
        uri = f'get_attachments_for_case/{case_id}'
        params = []
        if limit is not None:
            params.append(f'limit={limit}')
        if offset is not None:
            params.append(f'offset={offset}')
        if params:
            uri += '&' + '&'.join(params)
        return self._send_request('GET', uri)

    def get_attachment(self, attachment_id: str) -> Dict:
        """Download an attachment by ID. Returns base64-encoded content."""
        response = self._send_request_raw('GET', f'get_attachment/{attachment_id}')
        return {
            'data': base64.b64encode(response.content).decode('ascii'),
            'content_type': response.headers.get('Content-Type', 'application/octet-stream'),
        }
