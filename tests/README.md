# Tests

This directory contains unit tests and integration tests for the ARK Agent AGI system.

## Running Tests

### Run all tests:
```bash
python -m pytest tests/
```

### Run specific test file:
```bash
python tests/test_builtin_tools.py
```

### Run with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Structure

- `test_builtin_tools.py` - Unit tests for all 11 built-in tools
- Tests cover:
  - Calculator Tool (arithmetic, advanced math, statistics)
  - Code Execution Tool (safety, imports, error handling)
  - Database Tool (queries, security)
  - Agent Controller (pause/resume, message queueing)
  - All other tools (graceful API key failures)

## Test Coverage

Current test coverage:
- **Calculator Tool**: 100%
- **Code Execution Tool**: 95%
- **Database Tool**: 100%
- **Agent Controller**: 100%
- **Other Tools**: API key fallback testing

Total: **40+ unit tests** covering all critical functionality.
