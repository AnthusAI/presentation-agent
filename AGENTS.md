# Agent Guidelines

This project follows a strict **Behavior Driven Development (BDD)** workflow.

As an agent working on this project, you **MUST** adhere to the following cycle for every new feature or modification:

1.  **Write the Spec First (RED)**:
    *   Create or update a `.feature` file in the `features/` directory.
    *   Define the desired behavior using Gherkin syntax (Given/When/Then).
    *   **Verify Failure**: Run the tests (`behave features/your_feature.feature`) and confirm they fail (or are undefined). Do *not* skip this step. Seeing the failure ensures your test is actually testing something.

2.  **Implement the Feature (GREEN)**:
    *   Write the minimum code necessary to implement the feature.
    *   Implement the step definitions in `features/steps/`.

3.  **Test and Refine (REFACTOR)**:
    *   Run the tests again.
    *   If new scenarios or edge cases are discovered during implementation, **add them to the feature file immediately** as failing tests, then make them pass.
    *   Ensure *all* tests pass before declaring the task complete.

## Project Structure
*   `features/`: BDD feature specifications.
*   `features/steps/`: Python step definitions for Behave.
*   `src/`: Source code.
*   `tests/`: Unit tests (optional, BDD is primary).

## Key Rules
*   **Never write code without a failing test.**
*   **Don't guess**; if a test fails, read the error, understand it, and fix the code or the test.
*   **Verify visually** if possible (e.g. "Run it and see") in addition to automated tests, but automated tests are the source of truth for behavior.

