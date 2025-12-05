# Contributing to DeckBot

Thank you for your interest in contributing to DeckBot! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/yourusername/deckbot.git
   cd deckbot
   conda create -n deckbot python=3.11
   conda activate deckbot
   pip install -e ".[dev]"
   ```

2. **Set up environment:**
   Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```

3. **Install external dependencies:**
   - Node.js and npm (for Marp CLI)
   - Chrome/Chromium (for PDF export)

## Development Workflow

This project follows **Behavior Driven Development (BDD)**. The workflow is:

### 1. Write the Spec First (RED)

Create or update a `.feature` file in `features/`:

```gherkin
Feature: Your Feature
  Scenario: What it should do
    Given some initial state
    When some action occurs
    Then the expected result happens
```

**Verify it fails:**
```bash
behave features/your_feature.feature
```

### 2. Implement the Feature (GREEN)

- Write step definitions in `features/steps/`
- Implement the actual code in `src/deckbot/`
- Run tests frequently

### 3. Test and Refine (REFACTOR)

Run tests until all pass:
```bash
behave
```

## Testing

### Unit/Feature Tests (Fast, No API Calls)

Run all tests:
```bash
behave
```

Run specific feature:
```bash
behave features/web_ui.feature
```

Run specific scenario:
```bash
behave features/web_ui.feature -n "Color Theme Selection"
```

Show output:
```bash
behave --no-capture
```

### Integration Tests (Slow, Requires API Key)

Integration tests make real API calls and are excluded by default:

```bash
./run_integration_tests.sh
```

Or manually:
```bash
behave --tags=integration features/image_generation_integration.feature
```

## Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning.

### Format

```
<type>(<scope>): <subject>
```

### Types

- **feat**: New feature (triggers MINOR version bump: 1.0.0 → 1.1.0)
- **fix**: Bug fix (triggers PATCH version bump: 1.0.0 → 1.0.1)
- **perf**: Performance improvement (triggers PATCH version bump)
- **docs**: Documentation only (no version bump)
- **style**: Code formatting (no version bump)
- **refactor**: Code refactoring (no version bump)
- **test**: Test changes (no version bump)
- **build**: Build system changes (no version bump)
- **ci**: CI configuration changes (no version bump)
- **chore**: Other changes (no version bump)

### Examples

**Feature (minor bump):**
```
feat(image-gen): add batch tracking for image generation
```

**Bug fix (patch bump):**
```
fix(web-ui): resolve template selection dropdown issue
```

**Breaking change (major bump):**
```
feat!: migrate to Python 3.11+ only

BREAKING CHANGE: Removed support for Python 3.9 and 3.10
```

See [`.github/COMMIT_CONVENTION.md`](.github/COMMIT_CONVENTION.md) for more details.

## Release Process

Releases are automated using GitHub Actions and Semantic Release:

1. **Make changes** following BDD workflow
2. **Commit** using conventional commit format
3. **Push to `main`** (or create PR)
4. **GitHub Actions** automatically:
   - Runs all tests
   - Analyzes commit messages
   - Bumps version if needed
   - Updates CHANGELOG.md
   - Creates GitHub release
   - Publishes to PyPI (if configured)

### Version Bumping

Versions are determined by commit messages:

| Commit Type | Version Change | Example |
|-------------|----------------|---------|
| `feat:` | 1.0.0 → 1.1.0 | Minor bump |
| `fix:` | 1.0.0 → 1.0.1 | Patch bump |
| `feat!:` or `BREAKING CHANGE:` | 1.0.0 → 2.0.0 | Major bump |
| `docs:`, `chore:`, etc. | No change | No release |

### Manual Release Testing

Test the release process locally:

```bash
# See what the next version would be
semantic-release version --print

# See unreleased changes
semantic-release changelog --unreleased
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Write tests for all new features

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-new-feature
   ```
3. **Make changes** following BDD workflow
4. **Run tests** and ensure they all pass:
   ```bash
   behave
   ```
5. **Commit** using conventional commit format
6. **Push** to your fork
7. **Create Pull Request** to `main` branch
8. **Wait for CI** to pass
9. **Address review** comments if any

### PR Title

PR titles should also follow conventional commits format:

```
feat(web-ui): add dark mode support
fix(cli): resolve export command crash
```

## Questions?

- Read the [README.md](README.md) for project overview
- Check [.github/WORKFLOWS.md](.github/WORKFLOWS.md) for CI/CD details
- Review existing feature files in `features/` for examples
- Open an issue for questions or suggestions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).




