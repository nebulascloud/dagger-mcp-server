"""
Test fixtures for OpenAI MCP Demo application.

Provides comprehensive test data for Jira API responses, OpenAI interactions,
and other test scenarios.
"""

import json
from typing import Dict, List, Any


class JiraFixtures:
    """Mock Jira API response fixtures."""

    @staticmethod
    def get_projects_response() -> Dict[str, Any]:
        """Mock response for Jira projects list."""
        return {
            "projects": [
                {
                    "id": "10001",
                    "key": "MCP",
                    "name": "MCP Development",
                    "description": "Model Context Protocol development project",
                    "projectTypeKey": "software"
                },
                {
                    "id": "10002", 
                    "key": "DEMO",
                    "name": "Demo Applications",
                    "description": "Demonstration applications and examples",
                    "projectTypeKey": "software"
                },
                {
                    "id": "10003",
                    "key": "TEST",
                    "name": "Testing Infrastructure", 
                    "description": "Testing and quality assurance project",
                    "projectTypeKey": "software"
                }
            ]
        }

    @staticmethod
    def get_issues_response() -> Dict[str, Any]:
        """Mock response for Jira issues in MCP project."""
        return {
            "issues": [
                {
                    "id": "10100",
                    "key": "MCP-374",
                    "fields": {
                        "summary": "Implement Dagger Multistage CI Pipeline for MCP Applications",
                        "description": "Epic for implementing comprehensive CI/CD pipeline using Dagger",
                        "status": {"name": "In Progress"},
                        "priority": {"name": "High"},
                        "issuetype": {"name": "Epic"},
                        "assignee": {"displayName": "Development Team"},
                        "created": "2024-01-01T10:00:00.000Z",
                        "updated": "2024-01-15T14:30:00.000Z"
                    }
                },
                {
                    "id": "10101", 
                    "key": "MCP-376",
                    "fields": {
                        "summary": "Implement Code Quality Stage",
                        "description": "Add linting, formatting, and static analysis to Dagger pipeline",
                        "status": {"name": "Done"},
                        "priority": {"name": "High"},
                        "issuetype": {"name": "Story"},
                        "assignee": {"displayName": "QA Team"},
                        "created": "2024-01-02T09:00:00.000Z",
                        "updated": "2024-01-10T16:45:00.000Z"
                    }
                },
                {
                    "id": "10102",
                    "key": "MCP-377", 
                    "fields": {
                        "summary": "Implement Testing Stage - Unit Tests, Integration Tests, and Coverage",
                        "description": "Comprehensive testing infrastructure with Dagger-native optimization",
                        "status": {"name": "In Progress"},
                        "priority": {"name": "High"},
                        "issuetype": {"name": "Story"},
                        "assignee": {"displayName": "Test Engineer"},
                        "created": "2024-01-03T11:15:00.000Z",
                        "updated": "2024-01-16T13:20:00.000Z"
                    }
                },
                {
                    "id": "10103",
                    "key": "MCP-378",
                    "fields": {
                        "summary": "Implement Deployment Stage",
                        "description": "Add deployment automation and environment management",
                        "status": {"name": "To Do"},
                        "priority": {"name": "Medium"},
                        "issuetype": {"name": "Story"},
                        "assignee": {"displayName": "DevOps Team"},
                        "created": "2024-01-04T08:30:00.000Z",
                        "updated": "2024-01-04T08:30:00.000Z"
                    }
                },
                {
                    "id": "10104",
                    "key": "MCP-379",
                    "fields": {
                        "summary": "Setup Monitoring and Alerting",
                        "description": "Implement comprehensive monitoring for the CI/CD pipeline",
                        "status": {"name": "To Do"},
                        "priority": {"name": "Low"},
                        "issuetype": {"name": "Task"},
                        "assignee": {"displayName": "SRE Team"},
                        "created": "2024-01-05T12:45:00.000Z",
                        "updated": "2024-01-05T12:45:00.000Z"
                    }
                }
            ]
        }

    @staticmethod
    def get_issue_link_types_response() -> Dict[str, Any]:
        """Mock response for available issue link types."""
        return {
            "issueLinkTypes": [
                {
                    "id": "10000",
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks"
                },
                {
                    "id": "10001", 
                    "name": "Depends on",
                    "inward": "depends on",
                    "outward": "is dependency of"
                },
                {
                    "id": "10002",
                    "name": "Relates",
                    "inward": "relates to",
                    "outward": "relates to"
                },
                {
                    "id": "10003",
                    "name": "Duplicates",
                    "inward": "is duplicated by", 
                    "outward": "duplicates"
                }
            ]
        }

    @staticmethod
    def get_create_link_success_response() -> Dict[str, Any]:
        """Mock response for successful link creation."""
        return {
            "id": "20001",
            "type": {
                "id": "10001",
                "name": "Depends on",
                "inward": "depends on",
                "outward": "is dependency of"
            },
            "inwardIssue": {
                "id": "10102",
                "key": "MCP-377"
            },
            "outwardIssue": {
                "id": "10101", 
                "key": "MCP-376"
            }
        }

    @staticmethod
    def get_dependency_analysis_scenario() -> List[Dict[str, Any]]:
        """Complete scenario data for dependency analysis testing."""
        return [
            {
                "step": "get_projects",
                "description": "User requests available projects",
                "query": "What Jira projects do I have access to?",
                "response": JiraFixtures.get_projects_response(),
                "expected_output": "You have access to 3 Jira projects: MCP Development, Demo Applications, Testing Infrastructure"
            },
            {
                "step": "get_issues",
                "description": "User requests issues in MCP project", 
                "query": "Show me issues in the MCP project",
                "response": JiraFixtures.get_issues_response(),
                "expected_output": "Here are 5 issues in the MCP project"
            },
            {
                "step": "analyze_dependencies",
                "description": "User requests dependency analysis",
                "query": "Based on these issues, suggest where dependencies should be set",
                "response": None,  # This would be OpenAI analysis
                "expected_output": "MCP-377 should depend on MCP-376"
            },
            {
                "step": "get_link_types",
                "description": "System checks available link types",
                "query": "What issue link types are available?",
                "response": JiraFixtures.get_issue_link_types_response(),
                "expected_output": "Available link types: Blocks, Depends on, Relates, Duplicates"
            },
            {
                "step": "create_link",
                "description": "System creates the suggested dependency",
                "query": "Create a dependency link between MCP-377 and MCP-376",
                "response": JiraFixtures.get_create_link_success_response(),
                "expected_output": "Successfully created dependency link"
            }
        ]


class OpenAIFixtures:
    """Mock OpenAI API response fixtures."""

    @staticmethod
    def get_analysis_response() -> Dict[str, Any]:
        """Mock OpenAI response for dependency analysis."""
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": """Based on the analysis of the MCP project issues, here are the recommended dependencies:

**Critical Dependencies:**
1. **MCP-377 (Testing Stage)** should depend on **MCP-376 (Code Quality Stage)**
   - Rationale: Testing infrastructure needs code quality tools to be in place first
   - Link Type: "Depends on"

2. **MCP-378 (Deployment Stage)** should depend on **MCP-377 (Testing Stage)**
   - Rationale: Deployment should only happen after comprehensive testing is available
   - Link Type: "Depends on"

3. **MCP-379 (Monitoring)** should depend on **MCP-378 (Deployment Stage)**
   - Rationale: Monitoring setup requires deployment infrastructure to be completed
   - Link Type: "Depends on"

**Sequential Implementation Order:**
MCP-376 → MCP-377 → MCP-378 → MCP-379

All of these should relate back to the epic MCP-374."""
                    }
                }
            ]
        }

    @staticmethod
    def get_project_list_response() -> Dict[str, Any]:
        """Mock OpenAI response for project listing."""
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": """You have access to the following Jira projects:

🏗️ **MCP Development (MCP)**
   - Primary development project for Model Context Protocol
   - 5 active issues, focusing on CI/CD pipeline implementation

🎯 **Demo Applications (DEMO)**  
   - Example applications and proof-of-concepts
   - 2 open issues related to documentation and examples

🧪 **Testing Infrastructure (TEST)**
   - Quality assurance and testing automation
   - 3 issues covering test automation and infrastructure

Each project has different focuses and priorities. The MCP project is currently the most active with the CI/CD pipeline epic in progress."""
                    }
                }
            ]
        }

    @staticmethod
    def get_link_creation_response() -> Dict[str, Any]:
        """Mock OpenAI response for successful link creation."""
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant", 
                        "content": """✅ **Dependency Link Created Successfully!**

**Link Details:**
- **From:** MCP-377 (Testing Stage Implementation)  
- **To:** MCP-376 (Code Quality Stage)
- **Link Type:** "Depends on"
- **Direction:** MCP-377 depends on MCP-376

**What This Means:**
The Testing Stage (MCP-377) now has a formal dependency on the Code Quality Stage (MCP-376). This ensures that:

1. Code quality tools and standards are established before testing implementation
2. The testing infrastructure can leverage the linting and formatting setup
3. Project workflow reflects the logical implementation sequence

The dependency relationship will help with project planning and ensure proper implementation order."""
                    }
                }
            ]
        }

    @staticmethod
    def get_error_recovery_response() -> Dict[str, Any]:
        """Mock OpenAI response for error recovery scenario."""
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": """I encountered an issue with the link type "Depends". Let me try using "Depends on" instead, which is a more common link type in Jira.

🔄 **Attempting Recovery...**

Let me check the available link types first and then create the dependency using the correct type name."""
                    }
                }
            ]
        }


class TestScenarios:
    """Complete test scenarios combining Jira and OpenAI fixtures."""

    @staticmethod
    def get_happy_path_scenario() -> Dict[str, Any]:
        """Complete happy path test scenario."""
        return {
            "name": "Complete Dependency Analysis - Happy Path",
            "description": "User successfully analyzes project, identifies dependencies, and creates links",
            "steps": [
                {
                    "action": "query_projects",
                    "user_input": "What Jira projects are available?",
                    "mock_responses": {
                        "jira": JiraFixtures.get_projects_response(),
                        "openai": OpenAIFixtures.get_project_list_response()
                    },
                    "expected_contains": ["MCP Development", "Demo Applications", "Testing Infrastructure"]
                },
                {
                    "action": "query_issues",
                    "user_input": "Show me issues in the MCP project",
                    "mock_responses": {
                        "jira": JiraFixtures.get_issues_response(),
                        "openai": None  # Would be processed by formatting
                    },
                    "expected_contains": ["MCP-374", "MCP-376", "MCP-377", "Epic", "Testing Stage"]
                },
                {
                    "action": "analyze_dependencies", 
                    "user_input": "Suggest dependencies based on these issues",
                    "mock_responses": {
                        "jira": None,
                        "openai": OpenAIFixtures.get_analysis_response()
                    },
                    "expected_contains": ["MCP-377", "depend", "MCP-376", "Code Quality"]
                },
                {
                    "action": "create_dependency",
                    "user_input": "Create the suggested dependency link",
                    "mock_responses": {
                        "jira": JiraFixtures.get_create_link_success_response(),
                        "openai": OpenAIFixtures.get_link_creation_response()
                    },
                    "expected_contains": ["Successfully created", "MCP-377", "MCP-376", "Depends on"]
                }
            ],
            "final_state": {
                "conversation_length": 4,
                "dependencies_created": 1,
                "success": True
            }
        }

    @staticmethod
    def get_error_recovery_scenario() -> Dict[str, Any]:
        """Error recovery test scenario."""
        return {
            "name": "Link Creation Error Recovery",
            "description": "System recovers from link type errors and retries with correct type",
            "steps": [
                {
                    "action": "attempt_link_creation",
                    "user_input": "Create dependency between MCP-377 and MCP-376",
                    "mock_responses": {
                        "jira": {"error": "Invalid link type 'Depends'"},
                        "openai": OpenAIFixtures.get_error_recovery_response()
                    },
                    "expected_contains": ["error", "recovery", "try using"]
                },
                {
                    "action": "check_link_types",
                    "user_input": "What link types are available?",
                    "mock_responses": {
                        "jira": JiraFixtures.get_issue_link_types_response(),
                        "openai": None
                    },
                    "expected_contains": ["Blocks", "Depends on", "Relates", "Duplicates"]
                },
                {
                    "action": "retry_link_creation",
                    "user_input": "Create link using 'Depends on' type",
                    "mock_responses": {
                        "jira": JiraFixtures.get_create_link_success_response(),
                        "openai": OpenAIFixtures.get_link_creation_response()
                    },
                    "expected_contains": ["Successfully created", "Depends on"]
                }
            ],
            "final_state": {
                "conversation_length": 3,
                "dependencies_created": 1,
                "recovery_successful": True
            }
        }

    @staticmethod
    def get_performance_test_data() -> Dict[str, Any]:
        """Large dataset for performance testing."""
        # Generate large issue set
        issues = []
        for i in range(1, 101):  # 100 issues
            issues.append({
                "id": f"1{i:04d}",
                "key": f"MCP-{i+400}",
                "fields": {
                    "summary": f"Performance Test Issue {i}",
                    "description": f"This is a performance test issue number {i} with detailed description " + "x" * 1000,
                    "status": {"name": "To Do" if i % 3 == 0 else "In Progress"},
                    "priority": {"name": "High" if i % 5 == 0 else "Medium"},
                    "issuetype": {"name": "Story"},
                    "assignee": {"displayName": f"User {i % 10}"},
                    "created": f"2024-01-{(i % 30) + 1:02d}T10:00:00.000Z",
                    "updated": f"2024-01-{(i % 30) + 1:02d}T15:30:00.000Z"
                }
            })

        return {
            "name": "Performance Test Dataset", 
            "description": "Large dataset for performance and scalability testing",
            "data": {
                "projects": JiraFixtures.get_projects_response(),
                "issues": {"issues": issues},
                "link_types": JiraFixtures.get_issue_link_types_response()
            },
            "metrics": {
                "issue_count": 100,
                "total_size_kb": len(json.dumps(issues)) // 1024,
                "max_description_length": 1100
            }
        }


class MockResponses:
    """Utilities for creating mock API responses."""

    @staticmethod
    def create_jira_error(error_code: int, message: str) -> Dict[str, Any]:
        """Create mock Jira error response."""
        return {
            "errorMessages": [message],
            "errors": {},
            "httpStatusCode": error_code
        }

    @staticmethod
    def create_openai_error(error_type: str, message: str) -> Dict[str, Any]:
        """Create mock OpenAI error response."""
        return {
            "error": {
                "type": error_type,
                "message": message,
                "code": error_type.upper()
            }
        }

    @staticmethod
    def create_network_timeout_scenario() -> Dict[str, Any]:
        """Create network timeout test scenario."""
        return {
            "name": "Network Timeout Recovery",
            "description": "Test recovery from network timeouts",
            "delays": [5.0, 3.0, 1.0],  # Decreasing delays for retry logic
            "final_success": True
        }


if __name__ == "__main__":
    # Example usage and validation
    print("=== Test Fixtures Examples ===")
    
    print("\n1. Jira Projects:")
    projects = JiraFixtures.get_projects_response()
    print(f"   Found {len(projects['projects'])} projects")
    
    print("\n2. Jira Issues:")
    issues = JiraFixtures.get_issues_response()
    print(f"   Found {len(issues['issues'])} issues")
    
    print("\n3. Complete Scenario:")
    scenario = TestScenarios.get_happy_path_scenario()
    print(f"   Scenario: {scenario['name']}")
    print(f"   Steps: {len(scenario['steps'])}")
    
    print("\n4. Performance Data:")
    perf_data = TestScenarios.get_performance_test_data()
    print(f"   Issues: {perf_data['metrics']['issue_count']}")
    print(f"   Size: {perf_data['metrics']['total_size_kb']} KB")
    
    print("\n✅ All fixtures validated successfully!")