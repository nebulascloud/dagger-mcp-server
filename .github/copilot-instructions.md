# Copilot Instructions

## General Jira Guidelines
*   **Issue Descriptions:** Provide a comprehensive description that outlines the task's purpose, the problem it solves, and the proposed approach. It should provide enough context for a developer to begin work.
*   **Issue Task Scheduling** If the user's request or the surrounding context provides explicit timelines, estimates, or target dates, use this information to set a `duedate`. **Do not invent dates.** If no such information is available, leave the due date blank to be determined by the project team.
*   **Setting Dependencies** If a task's dependencies are understood, create the necessary issue links.
    *   If a new task depends on an *existing* issue, the link can be created at the same time as the task using the `issuelinks` field.
    *   If new tasks depend on *each other* within the same batch, create them first, then use the `create_issue_link` tool in a separate, subsequent step to establish the dependencies.

## Development Workflow
*   **Task Status Updates:** It is critical to keep Jira statuses aligned with the development process.
    *   **Start Work:** Before beginning implementation on a Jira task, first transition its status to "In Progress".
    *   **Git Branching:** Never make any changes directly to the main branch and instead check that the current feature/fix branch is fit for purpose else create a new one.
    *   **Complete Work:** Upon successful completion and testing of a task, transition its status to "Done".
    *   **Sequential Progress:** Before starting the next task, ensure it is marked as "In Progress". This provides clear visibility into what is currently being worked on.
    *   **User Validation:** After implementing a task, do not transition it to "Done" or start the next task until the user has explicitly confirmed the work is complete and satisfactory. Await user approval before proceeding.
    *   **Commits:** After a task is validated and marked as "Done", create a Git commit with a descriptive message summarizing the changes. This creates a clear history of the project's progress.

### Epics
*   **Parent Link:** All tasks that belong to an epic must be linked to their parent epic upon creation.
*   **Labels:** Include `task`, and any other relevant technology or project labels.
    *   **Do not include redundant headings** like 'Description', as this is already part of the Jira UI. The content should begin directly.
    *   The description must be more than a single sentence and should be followed by a distinct `h3. Acceptance Criteria` section.
*   **Acceptance Criteria:** Define clear and measurable acceptance criteria that can be used to verify that the task has been completed successfully.

## Code
*   **Style:** Follow the PEP 8 style guide for Python code.
*   **Documentation:** All functions and classes should have docstrings.
    *   Docstrings for tool functions should follow a consistent format (e.g., Google Style, reStructuredText) to ensure they can be reliably parsed into a machine-readable manifest.
*   **Testing:** All new features should be accompanied by unit tests.
    *   Unit tests for MCP tools must validate that all parameters, especially nested dictionaries like `additional_fields`, are correctly processed and passed to the underlying API client.

## Tooling & Manifests

*   **Comprehensive Documentation:** Tool docstrings must be comprehensive and reflect all capabilities of the underlying function. All parameters, including all possible keys in dictionary parameters (like `additional_fields`), must be documented.
*   **Rich Examples:** The description for each tool parameter should include rich examples covering common and complex use cases (e.g., setting a parent link, adding custom fields, setting dates).
*   **Manifest-Driven Development:** The auto-generated tool manifest (e.g., OpenAPI spec) is the single source of truth for tool capabilities. If a feature isn't in the manifest, it doesn't exist.