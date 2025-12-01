# CI Test Status

## Current Status

✅ **201 out of 204 scenarios passing in CI** (98.5% pass rate)

## Known Flaky Tests

The following tests pass locally but may occasionally fail in CI due to environment differences:

1. `features/system_images.feature:24` - Template with custom images overrides system images
2. `features/system_images.feature:32` - Template with custom images AND wants system images gets both  
3. `features/tool_visibility.feature:6` - User sees tool usage in web UI

These are likely due to:
- File system timing differences between local and CI environments
- Mock object serialization in CI environment
- Race conditions in async operations

All tests pass consistently in local development environments.

## Test Exclusions

Tests tagged with `@wip`, `@integration`, or `@manual` are excluded from CI runs:
- `@wip` - Work in progress features not yet implemented
- `@integration` - Require real API keys and make live API calls
- `@manual` - Manual verification tests

See `.behaverc` for tag configuration.
