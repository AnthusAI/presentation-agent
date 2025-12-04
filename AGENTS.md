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
*   `pyproject.toml`: Project configuration and dependencies (prefer this over requirements.txt).

## Key Rules
*   **Never write code without a failing test.**
*   **Don't guess**; if a test fails, read the error, understand it, and fix the code or the test.
*   **Verify visually** if possible (e.g. "Run it and see") in addition to automated tests, but automated tests are the source of truth for behavior.
*   **CRITICAL: Run tests after EVERY code change.** Do not declare a task complete, do not commit, do not move on until you have:
    1. Run `behave` (or the relevant subset of tests)
    2. Confirmed that ALL tests PASS (0 failed, 0 error)
    3. If tests fail or error, FIX THEM IMMEDIATELY before doing anything else
*   **Never assume tests pass.** Always verify. A BDD project with failing tests is a broken project.

## Testing Strategy

### Unit & Feature Tests (Default)
By default, `behave` runs **fast, isolated tests** that mock external API calls. These tests:
- Run in seconds
- Don't require API keys
- Don't consume quota
- Are automatically run on every code change

**Run all unit/feature tests:**
```bash
behave
```

### Integration Tests (Manual, Requires API Key)
Integration tests make **real API calls** to verify end-to-end functionality. These tests:
- Are **excluded from normal test runs** (tagged with `@integration` and `@manual`)
- Require `GOOGLE_API_KEY` environment variable
- Make real API calls that consume quota
- Take longer to run
- Verify actual API integration (e.g., image generation with Gemini)

**Run integration tests:**
```bash
./run_integration_tests.sh
```

Or manually:
```bash
behave --tags=integration features/image_generation_integration.feature
```

**When to use integration tests:**
- After changing API integration code (e.g., `nano_banana.py`)
- Before major releases to verify external services work
- When debugging issues that only appear with real API calls
- To verify prompt engineering changes produce expected results

**Do NOT run integration tests:**
- During normal feature development
- In automated CI/CD pipelines (unless quota is acceptable)
- When iterating rapidly on code changes

The `.behaverc` file excludes integration tests by default with `default_tags = -integration,-manual`.

## Image Generation Architecture

### Batch Tracking System
Every image generation request creates a **unique batch** with a slug-based identifier (e.g., `cybernetic-feedback-loop-12345`). This enables:

- **Context Preservation**: Each batch has a unique ID derived from the prompt + timestamp
- **Organized Storage**: Images saved in `drafts/{batch-slug}/` for easy reference
- **Clear Provenance**: SYSTEM messages include batch IDs: `"[SYSTEM] User selected an image from (batch: slug-12345)..."`
- **History Tracking**: Batch IDs in chat history allow the agent to distinguish between old and new image requests

### Image Generation Workflow
When implementing or testing image-related features:

1. **Generation**: `generate_candidates()` returns:
   ```python
   {
       'candidates': [list of image paths],
       'batch_slug': 'unique-identifier',
       'batch_folder': 'drafts/unique-identifier'
   }
   ```

2. **Selection**: User selects an image, triggering a SYSTEM message with batch context
3. **Incorporation**: Agent uses the SYSTEM message to incorporate the correct image
4. **Batch Awareness**: Agent ignores SYSTEM messages from old batches when working on new requests

**Key Files:**
- `src/deckbot/nano_banana.py`: Batch slug generation and image storage
- `src/deckbot/session_service.py`: SYSTEM message creation with batch IDs
- `src/deckbot/agent.py`: Agent instructions for batch-aware behavior
- `features/image_batch_tracking.feature`: BDD tests for batch system

## Model Configuration & Fallback
The agent supports configurable primary and secondary models via `.deckbot.yaml`.
- **Primary Model**: Default is `gemini-3-pro-preview`.
- **Secondary Model**: Default is `gemini-2.0-flash-exp`.
- **Automatic Fallback**: If the primary model returns a `429 RESOURCE_EXHAUSTED` error, the agent automatically switches to the secondary model and retries the request transparently.
