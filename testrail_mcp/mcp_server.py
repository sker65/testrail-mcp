"""MCP server implementation for TestRail."""
from typing import Dict, List, Any, Optional, Union
from fastmcp import FastMCP

from testrail_mcp.testrail_client import TestRailClient
from testrail_mcp.config import (
    TESTRAIL_URL,
    TESTRAIL_USERNAME,
    TESTRAIL_API_KEY,
    TESTRAIL_MCP_ALLOW_DELETES,
    TESTRAIL_ALLOWED_PROJECT_IDS,
)


class TestRailMCPServer(FastMCP):
    """MCP server for TestRail integration using FastMCP."""
    
    def __init__(self):
        """Initialize the TestRail MCP server."""
        super().__init__(name="TestRail MCP Server", version="0.1.3")
        self.client = TestRailClient(TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY)
        self._register_tools()
        self._register_resources()

    def _ensure_project_allowed(self, project_id: int, operation: str) -> None:
        """Reject writes outside TESTRAIL_ALLOWED_PROJECT_IDS when configured."""
        if not TESTRAIL_ALLOWED_PROJECT_IDS:
            return

        try:
            project_id = int(project_id)
        except (TypeError, ValueError) as exc:
            raise PermissionError(
                f"Cannot determine project for {operation}; refusing because "
                "TESTRAIL_ALLOWED_PROJECT_IDS is set."
            ) from exc

        if project_id not in TESTRAIL_ALLOWED_PROJECT_IDS:
            allowed_ids = ", ".join(
                str(allowed_id) for allowed_id in sorted(TESTRAIL_ALLOWED_PROJECT_IDS)
            )
            raise PermissionError(
                f"{operation} is not allowed for project {project_id}. "
                f"Allowed projects: {allowed_ids}."
            )

    def _ensure_case_allowed(self, case_id: int, operation: str) -> None:
        if TESTRAIL_ALLOWED_PROJECT_IDS:
            self._ensure_project_allowed(
                self._project_id_for_case(case_id, operation),
                operation
            )

    def _ensure_section_allowed(self, section_id: int, operation: str) -> None:
        if TESTRAIL_ALLOWED_PROJECT_IDS:
            self._ensure_project_allowed(
                self._project_id_for_section(section_id, operation),
                operation
            )

    def _ensure_run_allowed(self, run_id: int, operation: str) -> None:
        if TESTRAIL_ALLOWED_PROJECT_IDS:
            self._ensure_project_allowed(
                self._project_id_for_run(run_id, operation),
                operation
            )

    def _ensure_test_allowed(self, test_id: int, operation: str) -> None:
        if TESTRAIL_ALLOWED_PROJECT_IDS:
            self._ensure_project_allowed(
                self._project_id_for_test(test_id, operation),
                operation
            )

    def _ensure_dataset_allowed(self, dataset_id: int, operation: str) -> None:
        if TESTRAIL_ALLOWED_PROJECT_IDS:
            self._ensure_project_allowed(
                self._project_id_for_dataset(dataset_id, operation),
                operation
            )

    def _reject_project_creation_when_allowlisted(self, operation: str) -> None:
        if TESTRAIL_ALLOWED_PROJECT_IDS:
            raise PermissionError(
                f"{operation} is not allowed when TESTRAIL_ALLOWED_PROJECT_IDS "
                "is set because the new project cannot already be allowlisted."
            )

    def _project_id_from_payload(
        self,
        payload: Dict,
        entity_name: str,
        entity_id: int,
        operation: str
    ) -> int:
        project_id = payload.get('project_id')
        if project_id is None:
            raise PermissionError(
                f"Cannot determine project for {operation} on "
                f"{entity_name} {entity_id}; refusing because "
                "TESTRAIL_ALLOWED_PROJECT_IDS is set."
            )
        try:
            return int(project_id)
        except (TypeError, ValueError) as exc:
            raise PermissionError(
                f"Invalid project ID for {operation} on {entity_name} "
                f"{entity_id}; refusing because TESTRAIL_ALLOWED_PROJECT_IDS "
                "is set."
            ) from exc

    def _project_id_for_suite(self, suite_id: int, operation: str) -> int:
        suite = self.client.get_suite(suite_id)
        return self._project_id_from_payload(suite, "suite", suite_id, operation)

    def _project_id_for_section(self, section_id: int, operation: str) -> int:
        section = self.client.get_section(section_id)
        project_id = section.get('project_id')
        if project_id is not None:
            return self._project_id_from_payload(section, "section", section_id, operation)

        suite_id = section.get('suite_id')
        if suite_id is None:
            raise PermissionError(
                f"Cannot determine project for {operation} on section "
                f"{section_id}; refusing because TESTRAIL_ALLOWED_PROJECT_IDS "
                "is set."
            )
        return self._project_id_for_suite(suite_id, operation)

    def _project_id_for_case(self, case_id: int, operation: str) -> int:
        test_case = self.client.get_case(case_id)
        project_id = test_case.get('project_id')
        if project_id is not None:
            return self._project_id_from_payload(test_case, "case", case_id, operation)

        suite_id = test_case.get('suite_id')
        if suite_id is not None:
            return self._project_id_for_suite(suite_id, operation)

        section_id = test_case.get('section_id')
        if section_id is not None:
            return self._project_id_for_section(section_id, operation)

        raise PermissionError(
            f"Cannot determine project for {operation} on case {case_id}; "
            "refusing because TESTRAIL_ALLOWED_PROJECT_IDS is set."
        )

    def _project_id_for_run(self, run_id: int, operation: str) -> int:
        run = self.client.get_run(run_id)
        return self._project_id_from_payload(run, "run", run_id, operation)

    def _project_id_for_test(self, test_id: int, operation: str) -> int:
        test = self.client.get_test(test_id)
        project_id = test.get('project_id')
        if project_id is not None:
            return self._project_id_from_payload(test, "test", test_id, operation)

        run_id = test.get('run_id')
        if run_id is not None:
            return self._project_id_for_run(run_id, operation)

        raise PermissionError(
            f"Cannot determine project for {operation} on test {test_id}; "
            "refusing because TESTRAIL_ALLOWED_PROJECT_IDS is set."
        )

    def _project_id_for_dataset(self, dataset_id: int, operation: str) -> int:
        dataset = self.client.get_dataset(dataset_id)
        return self._project_id_from_payload(dataset, "dataset", dataset_id, operation)
    
    def _register_tools(self):
        """Register all TestRail tools with the MCP server."""
        # Project tools
        @self.tool("get_project", description="Get a project by ID")
        def get_project(project_id: int) -> Dict:
            """Get a project by ID."""
            return self.client.get_project(project_id)
        
        @self.tool("get_projects", description="Get all projects")
        def get_projects() -> List[Dict]:
            """Get all projects."""
            return self.client.get_projects()
        
        @self.tool("add_project", description="Add a new project")
        def add_project(
            name: str,
            announcement: Optional[str] = None,
            show_announcement: Optional[bool] = None,
            suite_mode: Optional[int] = None
        ) -> Dict:
            """
            Add a new project.
            
            Args:
                name: The name of the project
                announcement: The announcement of the project (optional)
                show_announcement: Whether to show the announcement (optional)
                suite_mode: The suite mode: 1 for single suite mode, 2 for single suite + baselines, 3 for multiple suites (optional)
            """
            self._reject_project_creation_when_allowlisted("add_project")
            data = {'name': name}
            if announcement is not None:
                data['announcement'] = announcement
            if show_announcement is not None:
                data['show_announcement'] = show_announcement
            if suite_mode is not None:
                data['suite_mode'] = suite_mode
            return self.client.add_project(data)
        
        @self.tool("update_project", description="Update an existing project")
        def update_project(
            project_id: int,
            name: Optional[str] = None,
            announcement: Optional[str] = None,
            show_announcement: Optional[bool] = None,
            is_completed: Optional[bool] = None
        ) -> Dict:
            """
            Update an existing project.
            
            Args:
                project_id: The ID of the project
                name: The name of the project (optional)
                announcement: The announcement of the project (optional)
                show_announcement: Whether to show the announcement (optional)
                is_completed: Whether the project is completed (optional)
            """
            self._ensure_project_allowed(project_id, "update_project")
            data = {}
            if name is not None:
                data['name'] = name
            if announcement is not None:
                data['announcement'] = announcement
            if show_announcement is not None:
                data['show_announcement'] = show_announcement
            if is_completed is not None:
                data['is_completed'] = is_completed
            return self.client.update_project(project_id, data)
        
        if TESTRAIL_MCP_ALLOW_DELETES:
            @self.tool("delete_project", description="Delete a project")
            def delete_project(project_id: int) -> Dict:
                """
                Delete a project.

                Args:
                    project_id: The ID of the project
                """
                self._ensure_project_allowed(project_id, "delete_project")
                return self.client.delete_project(project_id)
        
        # Case tools
        @self.tool("get_case", description="Get a test case by ID")
        def get_case(case_id: int) -> Dict:
            """
            Get a test case by ID.
            
            Args:
                case_id: The ID of the test case
            """
            return self.client.get_case(case_id)
        
        @self.tool("get_cases", description="Get all test cases for a project/suite")
        def get_cases(project_id: int, suite_id: Optional[int] = None) -> List[Dict]:
            """
            Get all test cases for a project/suite.
            
            Args:
                project_id: The ID of the project
                suite_id: The ID of the test suite (optional)
            """
            return self.client.get_cases(project_id, suite_id)
        
        @self.tool("add_case", description="Add a new test case")
        def add_case(
            section_id: int,
            title: str,
            type_id: Optional[int] = None,
            priority_id: Optional[int] = None,
            estimate: Optional[str] = None,
            milestone_id: Optional[int] = None,
            refs: Optional[str] = None,
            custom_steps: Optional[str] = None,
            custom_expected: Optional[str] = None,
            custom_steps_separated: Optional[List[Dict[str, str]]] = None,
            steps_separated: Optional[List[Dict[str, str]]] = None
        ) -> Dict:
            """
            Add a new test case.
            
            Args:
                section_id: The ID of the section
                title: The title of the test case
                type_id: The ID of the case type (optional)
                priority_id: The ID of the priority (optional)
                estimate: The estimate, e.g. '30s' or '1m 45s' (optional)
                milestone_id: The ID of the milestone (optional)
                refs: A comma-separated list of references (optional)
                custom_steps: Steps as string
                custom_expected: case expected result
                custom_steps_separated: A list of test steps (optional), each with fields:
                    - content: The text contents of the "Step" field
                    - expected: The text contents of the "Expected Result" field
                    - additional_info: The text contents of the "Additional Info" field
                    - refs: Reference information for the "References" field
                steps_separated: A list of test steps (optional), each with fields:
                    - content: The text contents of the "Step" field
                    - expected: The text contents of the "Expected Result" field
                    - additional_info: The text contents of the "Additional Info" field
                    - refs: Reference information for the "References" field
            """
            self._ensure_section_allowed(section_id, "add_case")
            data = {'title': title}
            if type_id is not None:
                data['type_id'] = type_id
            if priority_id is not None:
                data['priority_id'] = priority_id
            if estimate is not None:
                data['estimate'] = estimate
            if milestone_id is not None:
                data['milestone_id'] = milestone_id
            if refs is not None:
                data['refs'] = refs
            if custom_steps_separated is not None:
                data['custom_steps_separated'] = custom_steps_separated
            if steps_separated is not None:
                data['steps_separated'] = steps_separated
            if custom_steps is not None:
                data['custom_steps'] = custom_steps
            if custom_expected is not None:
                data['custom_expected'] = custom_expected
            return self.client.add_case(section_id, data)
        
        @self.tool("update_case", description="Update an existing test case")
        def update_case(
            case_id: int,
            title: Optional[str] = None,
            type_id: Optional[int] = None,
            priority_id: Optional[int] = None,
            estimate: Optional[str] = None,
            milestone_id: Optional[int] = None,
            refs: Optional[str] = None,
            custom_steps: Optional[str] = None,
            custom_expected: Optional[str] = None,
            custom_steps_separated: Optional[List[Dict[str, str]]] = None,
            steps_separated: Optional[List[Dict[str, str]]] = None
        ) -> Dict:
            """
            Update an existing test case.
            
            Args:
                case_id: The ID of the test case
                title: The title of the test case (optional)
                type_id: The ID of the case type (optional)
                priority_id: The ID of the priority (optional)
                estimate: The estimate, e.g. '30s' or '1m 45s' (optional)
                milestone_id: The ID of the milestone (optional)
                refs: A comma-separated list of references (optional)
                custom_expected: case expected result
                custom_steps_separated: A list of test steps (optional), each with fields:
                    - content: The text contents of the "Step" field
                    - expected: The text contents of the "Expected Result" field
                    - additional_info: The text contents of the "Additional Info" field
                    - refs: Reference information for the "References" field
                steps_separated: A list of test steps (optional), each with fields:
                    - content: The text contents of the "Step" field
                    - expected: The text contents of the "Expected Result" field
                    - additional_info: The text contents of the "Additional Info" field
                    - refs: Reference information for the "References" field
            """
            self._ensure_case_allowed(case_id, "update_case")
            data = {}
            if title is not None:
                data['title'] = title
            if type_id is not None:
                data['type_id'] = type_id
            if priority_id is not None:
                data['priority_id'] = priority_id
            if estimate is not None:
                data['estimate'] = estimate
            if milestone_id is not None:
                data['milestone_id'] = milestone_id
            if refs is not None:
                data['refs'] = refs
            if custom_steps_separated is not None:
                data['custom_steps_separated'] = custom_steps_separated
            if steps_separated is not None:
                data['steps_separated'] = steps_separated
            if custom_steps is not None:
                data['custom_steps'] = custom_steps
            if custom_expected is not None:
                data['custom_expected'] = custom_expected
            return self.client.update_case(case_id, data)
        
        if TESTRAIL_MCP_ALLOW_DELETES:
            @self.tool("delete_case", description="Delete a test case")
            def delete_case(case_id: int) -> Dict:
                """
                Delete a test case.

                Args:
                    case_id: The ID of the test case
                """
                self._ensure_case_allowed(case_id, "delete_case")
                return self.client.delete_case(case_id)
        # Section tools
        @self.tool("get_section", description="Retrieves details of a specific section by ID")
        def get_section(section_id: int) -> Dict:
            """
            Get a section by ID.
            
            Args:
                section_id: The ID of the section
            """
            return self.client.get_section(section_id)

        @self.tool("get_sections", description="Retrieves all sections for a specified project and or suite")
        def get_sections(
            project_id : int,
            suite_id: Optional[int] = None ) -> Dict:
            """
            Retrieves all sections for a specified project and suite
            
            Args:
                project_id: The ID of the project
                suite_id: The ID of the test suite (Optional)

            """
            return self.client.get_sections(project_id,suite_id)

        @self.tool("add_section", description="Creates a new section in a TestRail project")
        def add_section(
            project_id : int,
            name: str,
            description: str,
            suite_id: Optional[int] = None,
            parent_id: Optional[int] = None) -> Dict:
            """
            Retrieves all sections for a specified project and suite
            
            Args:
                project_id: The ID of the project
                name: Name of the section
                description: Description of the section
                suite_id: The ID of the test suite (Optional)
                parent_id: The ID of the parent

            """
            self._ensure_project_allowed(project_id, "add_section")
            data = {}
            data["name"] = name
            data["description"] = description
            if suite_id is not None:
                data["suite_id"] = suite_id
            if parent_id is not None:
                data["parent_id"] = parent_id

            return self.client.add_section(project_id,data)

        @self.tool("update_section", description="Updates an existing section")
        def update_section(
            section_id : int,
            name: Optional[str] = None,
            description: Optional[str] = None) -> Dict:
            """
            Updates an existing section
            
            Args:
                section_id: The ID of the section
                name: Name of the section
                description: Description of the section
            """
            self._ensure_section_allowed(section_id, "update_section")
            data = {}
            if name is not None:
                data["name"] = name
            if description is not None:
                data["description"] = description

            return self.client.update_section(section_id, data)

        @self.tool("preview_delete_section", description="Preview deleting a section")
        def preview_delete_section(section_id: int) -> Dict:
            """
            Preview the impact of deleting an existing section.
            
            Args:
                section_id: The ID of the section
            """
            self._ensure_section_allowed(section_id, "preview_delete_section")
            return self.client.delete_section(section_id, soft=True)

        if TESTRAIL_MCP_ALLOW_DELETES:
            @self.tool("delete_section", description="Preview or delete a section")
            def delete_section(
                section_id : int,
                confirm: Optional[str] = None) -> Dict:
                """
                Preview or delete an existing section.

                Args:
                    section_id: The ID of the section
                    confirm: Must exactly match DELETE SECTION <section_id> to actually delete. Otherwise this returns a soft-delete preview.
                """
                self._ensure_section_allowed(section_id, "delete_section")
                if confirm != f"DELETE SECTION {section_id}":
                    return self.client.delete_section(section_id, soft=True)

                return self.client.delete_section(section_id, soft=False)

        @self.tool("move_section", description="Moves a section to a new position in the test hierarchy")
        def move_section(
            section_id : int,
            parent_id : Optional[int],
            after_id : Optional[int]) -> Dict:
            """
            Moves a section to a new position in the test hierarchy
            
            Args:
                section_id: The ID of the section
                parent_id: ID of the new parent
                after_id: ID of the section to be moved after
            """
            self._ensure_section_allowed(section_id, "move_section")
            if parent_id is not None:
                self._ensure_section_allowed(parent_id, "move_section")
            if after_id is not None:
                self._ensure_section_allowed(after_id, "move_section")
            data = {}
            if parent_id is not None:
                data["parent_id"] = parent_id
            if after_id is not None:
                data["after_id"] = after_id

            return self.client.move_section(section_id, data)

        # Run tools
        @self.tool("get_run", description="Get a test run by ID")
        def get_run(run_id: int) -> Dict:
            """
            Get a test run by ID.
            
            Args:
                run_id: The ID of the test run
            """
            return self.client.get_run(run_id)
        
        @self.tool("get_runs", description="Get all test runs for a project")
        def get_runs(project_id: int) -> List[Dict]:
            """
            Get all test runs for a project.
            
            Args:
                project_id: The ID of the project
            """
            return self.client.get_runs(project_id)
        
        @self.tool("add_run", description="Add a new test run")
        def add_run(
            project_id: int,
            suite_id: int,
            name: str,
            description: Optional[str] = None,
            milestone_id: Optional[int] = None,
            assignedto_id: Optional[int] = None,
            include_all: Optional[bool] = None,
            case_ids: Optional[List[int]] = None
        ) -> Dict:
            """
            Add a new test run.
            
            Args:
                project_id: The ID of the project
                suite_id: The ID of the test suite
                name: The name of the test run
                description: The description of the test run (optional)
                milestone_id: The ID of the milestone (optional)
                assignedto_id: The ID of the user the test run should be assigned to (optional)
                include_all: True for including all test cases of the test suite and false for a custom case selection (default: true) (optional)
                case_ids: An array of case IDs for the custom case selection (optional)
            """
            self._ensure_project_allowed(project_id, "add_run")
            data = {
                'suite_id': suite_id,
                'name': name
            }
            if description is not None:
                data['description'] = description
            if milestone_id is not None:
                data['milestone_id'] = milestone_id
            if assignedto_id is not None:
                data['assignedto_id'] = assignedto_id
            if include_all is not None:
                data['include_all'] = include_all
            if case_ids is not None:
                data['case_ids'] = case_ids
            return self.client.add_run(project_id, data)
        
        @self.tool("update_run", description="Update an existing test run")
        def update_run(
            run_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            milestone_id: Optional[int] = None,
            assignedto_id: Optional[int] = None,
            include_all: Optional[bool] = None,
            case_ids: Optional[List[int]] = None
        ) -> Dict:
            """
            Update an existing test run.
            
            Args:
                run_id: The ID of the test run
                name: The name of the test run (optional)
                description: The description of the test run (optional)
                milestone_id: The ID of the milestone (optional)
                assignedto_id: The ID of the user the test run should be assigned to (optional)
                include_all: True for including all test cases of the test suite and false for a custom case selection (default: true) (optional)
                case_ids: An array of case IDs for the custom case selection (optional)
            """
            self._ensure_run_allowed(run_id, "update_run")
            data = {}
            if name is not None:
                data['name'] = name
            if description is not None:
                data['description'] = description
            if milestone_id is not None:
                data['milestone_id'] = milestone_id
            if assignedto_id is not None:
                data['assignedto_id'] = assignedto_id
            if include_all is not None:
                data['include_all'] = include_all
            if case_ids is not None:
                data['case_ids'] = case_ids
            return self.client.update_run(run_id, data)
        
        @self.tool("close_run", description="Close an existing test run")
        def close_run(run_id: int) -> Dict:
            """
            Close an existing test run.
            
            Args:
                run_id: The ID of the test run
            """
            self._ensure_run_allowed(run_id, "close_run")
            return self.client.close_run(run_id)
        
        if TESTRAIL_MCP_ALLOW_DELETES:
            @self.tool("delete_run", description="Delete a test run")
            def delete_run(run_id: int) -> Dict:
                """
                Delete a test run.

                Args:
                    run_id: The ID of the test run
                """
                self._ensure_run_allowed(run_id, "delete_run")
                return self.client.delete_run(run_id)
        
        # Results tools
        @self.tool("get_results", description="Get all test results for a test")
        def get_results(test_id: int) -> List[Dict]:
            """
            Get all test results for a test.
            
            Args:
                test_id: The ID of the test
            """
            return self.client.get_results(test_id)
        
        @self.tool("add_result", description="Add a new test result")
        def add_result(
            test_id: int,
            status_id: int,
            comment: Optional[str] = None,
            version: Optional[str] = None,
            elapsed: Optional[str] = None,
            defects: Optional[str] = None,
            assignedto_id: Optional[int] = None
        ) -> Dict:
            """
            Add a new test result.
            
            Args:
                test_id: The ID of the test
                status_id: The ID of the test status
                comment: The comment / description for the test result (optional)
                version: The version or build you tested against (optional)
                elapsed: The time it took to execute the test, e.g. '30s' or '1m 45s' (optional)
                defects: A comma-separated list of defects to link to the test result (optional)
                assignedto_id: The ID of a user the test should be assigned to (optional)
            """
            self._ensure_test_allowed(test_id, "add_result")
            data = {
                'status_id': status_id
            }
            if comment is not None:
                data['comment'] = comment
            if version is not None:
                data['version'] = version
            if elapsed is not None:
                data['elapsed'] = elapsed
            if defects is not None:
                data['defects'] = defects
            if assignedto_id is not None:
                data['assignedto_id'] = assignedto_id
            return self.client.add_result(test_id, data)
        
        # Dataset tools
        @self.tool("get_dataset", description="Get a dataset by ID")
        def get_dataset(dataset_id: int) -> Dict:
            """
            Get a dataset by ID.
            
            Args:
                dataset_id: The ID of the dataset
            """
            return self.client.get_dataset(dataset_id)
        
        @self.tool("get_datasets", description="Get all datasets for a project")
        def get_datasets(project_id: int) -> List[Dict]:
            """
            Get all datasets for a project.
            
            Args:
                project_id: The ID of the project
            """
            return self.client.get_datasets(project_id)
        
        @self.tool("add_dataset", description="Add a new dataset")
        def add_dataset(
            project_id: int,
            name: str,
            description: Optional[str] = None
        ) -> Dict:
            """
            Add a new dataset.
            
            Args:
                project_id: The ID of the project
                name: The name of the dataset
                description: The description of the dataset (optional)
            """
            self._ensure_project_allowed(project_id, "add_dataset")
            data = {
                'name': name
            }
            if description is not None:
                data['description'] = description
            return self.client.add_dataset(project_id, data)
        
        @self.tool("update_dataset", description="Update an existing dataset")
        def update_dataset(
            dataset_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None
        ) -> Dict:
            """
            Update an existing dataset.
            
            Args:
                dataset_id: The ID of the dataset
                name: The name of the dataset (optional)
                description: The description of the dataset (optional)
            """
            self._ensure_dataset_allowed(dataset_id, "update_dataset")
            data = {}
            if name is not None:
                data['name'] = name
            if description is not None:
                data['description'] = description
            return self.client.update_dataset(dataset_id, data)
        
        if TESTRAIL_MCP_ALLOW_DELETES:
            @self.tool("delete_dataset", description="Delete a dataset")
            def delete_dataset(dataset_id: int) -> Dict:
                """
                Delete a dataset.

                Args:
                    dataset_id: The ID of the dataset
                """
                self._ensure_dataset_allowed(dataset_id, "delete_dataset")
                return self.client.delete_dataset(dataset_id)
    
    def _register_resources(self):
        """Register all TestRail resources with the MCP server."""
        @self.resource("testrail://project/{project_id}")
        def get_project_resource(project_id: int) -> Dict:
            """
            Get a project by ID.
            
            Args:
                project_id: The ID of the project
            """
            return self.client.get_project(project_id)
        
        @self.resource("testrail://case/{case_id}")
        def get_case_resource(case_id: int) -> Dict:
            """
            Get a test case by ID.
            
            Args:
                case_id: The ID of the test case
            """
            return self.client.get_case(case_id)
        
        @self.resource("testrail://run/{run_id}")
        def get_run_resource(run_id: int) -> Dict:
            """
            Get a test run by ID.
            
            Args:
                run_id: The ID of the test run
            """
            return self.client.get_run(run_id)
        
        @self.resource("testrail://results/{test_id}")
        def get_results_resource(test_id: int) -> List[Dict]:
            """
            Get all test results for a test.
            
            Args:
                test_id: The ID of the test
            """
            return self.client.get_results(test_id)
        
        @self.resource("testrail://dataset/{dataset_id}")
        def get_dataset_resource(dataset_id: int) -> Dict:
            """
            Get a dataset by ID.
            
            Args:
                dataset_id: The ID of the dataset
            """
            return self.client.get_dataset(dataset_id)

