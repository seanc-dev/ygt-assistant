# Refactor & Cleanup Plan

## Overview

Centralize and streamline the codebase by removing duplication, cleaning outdated docs, improving maintainability, and aligning tests and CI.

## Tasks

### 1. Clean Up Old Plan Files

- Delete completed plan files in `cursor-plans/`:
  - `cli-output-improvement-plan.md`
  - `date-time-error-handling-plan.md`
  - `date-utils-plan.md`
  - `terminal-agent-integration-plan.md`

### 2. Update Test Configuration

- Register `recurring` pytest marker in `pytest.ini`:
  ```ini
  [pytest]
  minversion = 6.0
  addopts = -ra -q -m "not integration"
  testpaths = tests
  python_files = test_*.py
  markers =
      integration: mark tests as integration tests to exclude them from default runs
      recurring: mark tests as recurring events (daily, weekly, etc.)
  ```
- Ensure no unknown-marker warnings in CI

### 3. Extract CLI Output Helpers

- Create `utils/cli_output.py` with functions:
  - `format_events(events: List[str]) -> str`
  - `format_reminders(reminders: List[str]) -> str`
  - `print_events_and_reminders(events: List[str], reminders: List[str])`
- Refactor `main.py` to replace duplicated print loops with these helpers
- Add unit tests for formatting functions

### 4. Refactor Main Loop Dispatcher

- Abstract action handlers into a dispatcher module (`utils/command_dispatcher.py`)
- Replace large `if-elif` chain in `main.py` with a mapping from action to handler functions

### 5. Consolidate Fallback Parsing

- Review LLM fallback mapping in `interpret_command`
- Migrate verb-based fallback logic into the unified `parse_command` helper if appropriate

### 6. Improve Test Fixtures

- Add a `conftest.py` in `tests/` with fixtures:
  - `dummy_store` for EventKit stubs
  - `cli_runner` for CLI integration tests
- Refactor integration tests to use these fixtures and remove duplicated monkeypatch code

### 7. Code Quality & Documentation

- Audit all public functions and classes to ensure docstrings are present and accurate
- Add type hints throughout the codebase
- Run `flake8` and fix any lint errors
- Update `future_enhancements.md` to reference this plan

## Timeline

- **Phase 1 (This Week):** Tasks 1, 2, 3
- **Phase 2 (Next Week):** Tasks 4, 5
- **Phase 3 (Later):** Tasks 6, 7
