"""MCP server implementation for TestRail."""
from typing import Dict, List, Any, Optional, Union
from fastmcp import FastMCP

from testrail_mcp.testrail_client import TestRailClient
from testrail_mcp.config import TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY


class TestRailMCPServer(FastMCP):
    """MCP server for TestRail integration using FastMCP."""
    
    def __init__(self):
        """Initialize the TestRail MCP server."""
        super().__init__(name="TestRail MCP Server", version="0.1.2")
        self.client = TestRailClient(TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY)
        self._register_tools()
        self._register_resources()
    
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
        
        @self.tool("delete_project", description="Delete a project")
        def delete_project(project_id: int) -> Dict:
            """
            Delete a project.
            
            Args:
                project_id: The ID of the project
            """
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
            refs: Optional[str] = None
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
            """
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
            return self.client.add_case(section_id, data)
        
        @self.tool("update_case", description="Update an existing test case")
        def update_case(
            case_id: int,
            title: Optional[str] = None,
            type_id: Optional[int] = None,
            priority_id: Optional[int] = None,
            estimate: Optional[str] = None,
            milestone_id: Optional[int] = None,
            refs: Optional[str] = None
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
            """
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
            return self.client.update_case(case_id, data)
        
        @self.tool("delete_case", description="Delete a test case")
        def delete_case(case_id: int) -> Dict:
            """
            Delete a test case.
            
            Args:
                case_id: The ID of the test case
            """
            return self.client.delete_case(case_id)
        
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
            return self.client.close_run(run_id)
        
        @self.tool("delete_run", description="Delete a test run")
        def delete_run(run_id: int) -> Dict:
            """
            Delete a test run.
            
            Args:
                run_id: The ID of the test run
            """
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
            data = {}
            if name is not None:
                data['name'] = name
            if description is not None:
                data['description'] = description
            return self.client.update_dataset(dataset_id, data)
        
        @self.tool("delete_dataset", description="Delete a dataset")
        def delete_dataset(dataset_id: int) -> Dict:
            """
            Delete a dataset.
            
            Args:
                dataset_id: The ID of the dataset
            """
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