# LLM Testing Framework

## Overview

The LLM testing framework provides end-to-end testing for assistant chat and LLM operations functionality. Tests use YAML scenario definitions and deterministic fixtures to ensure reproducible, fast test runs.

## Testing Structure

The testing framework follows a three-tier evaluation strategy:

1. **LLM Chat Responses** → Agent Evaluator
   - Uses GPT-4o-mini agent evaluator (when `LLM_EVAL_API_KEY` is available)
   - Assesses suitability, safety, and clarity of LLM-generated chat responses
   - Falls back to offline string matching (`must_contain`/`must_not_contain`) if unavailable
   - Full transcript snapshots are NOT enforced with live LLM (responses are non-deterministic)

2. **LLM Operations** → Deterministic Tests
   - Uses deterministic validation (`_assess_function_calling()`)
   - Validates operation structure (`op`, `params` fields), enum values, and user intent matching
   - Operation snapshots only enforced with fixtures (`LLM_TESTING_MODE=true`)
   - Always validates enum values and required parameters regardless of mode

3. **Infrastructure** → Fixtures
   - Uses `LLM_TESTING_MODE=true` (deterministic fixtures) by default
   - Full transcript snapshots enforced for regression testing
   - Tests HTTP flow, JSONPath extraction, database operations, execution logic
   - No live LLM calls - pure infrastructure validation

## Running Tests

### Run All Scenarios

```bash
make llm-run
```

### Run Assistant Chat & LLM Ops E2E Tests

```bash
make chat-llm-e2e
```

### Run Specific Scenarios

```bash
python -m llm_testing.runner --scenarios \
  llm_testing/scenarios/assistant_chat_happy_path.yaml \
  llm_testing/scenarios/llm_ops_task_training_wheels.yaml
```

## Test Structure

### Scenarios

Scenarios are defined in YAML files under `llm_testing/scenarios/`. Each scenario includes:

- **name**: Unique scenario identifier
- **mode**: `mock` for deterministic testing
- **snapshot**: Optional path to snapshot file for regression testing
- **env**: Optional environment variables to set
- **use_llm_fixtures**: Optional boolean (default: `true`). Set to `false` to test actual LLM behavior with live API calls
- **steps**: List of actions to execute
- **expectations**: Overall expectations for the scenario

#### Testing with Live LLM Calls

By default, scenarios use deterministic fixtures (`LLM_TESTING_MODE=true`) to test infrastructure without API costs. To test actual LLM behavior, set `use_llm_fixtures: false` in your scenario:

```yaml
name: llm_ops_task_real_llm
use_llm_fixtures: false # Use live LLM calls
env:
  OPENAI_API_KEY: ${OPENAI_API_KEY} # Required for live calls
steps:
  # ... test steps that require LLM to parse and respond correctly
```

When `use_llm_fixtures: false`:

- Tests will make real API calls to OpenAI (requires `OPENAI_API_KEY`)
- Tests both LLM behavior AND infrastructure
- Slower and incurs API costs
- Results may vary between runs
- Use for testing prompt quality, LLM understanding, and response accuracy

### Steps

Each step can be one of:

- **reset_state**: Clear in-memory state stores
- **http**: Make an HTTP request with assertions
- **grade**: Add expectations for evaluation

### HTTP Steps

HTTP steps support:

- **method**: HTTP method (GET, POST, PUT, DELETE)
- **url**: Endpoint URL (supports variable substitution with `<var_name>`)
- **params**: Query parameters
- **json**: Request body
- **extract**: Extract variables from response using JSONPath
- **expect**: Assertions:
  - **status**: Expected HTTP status code
  - **contains**: List of strings that must appear in response
  - **jsonpath**: JSONPath assertions

### Snapshots

Snapshots capture normalized transcripts (with timestamps and UUIDs replaced) for regression testing. They are stored in `llm_testing/snapshots/` and automatically created on first run.

**Snapshot behavior:**
- **Full transcript snapshots**: Only enforced with fixtures (`LLM_TESTING_MODE=true`) for infrastructure regression testing. With live LLM, snapshots generate warnings but don't fail tests (chat responses vary).
- **Operation snapshots**: Only enforced with fixtures for deterministic operation structure validation. With live LLM, snapshots generate warnings but don't fail tests (operation content may vary).

## LLM Operations

The LLM can propose various operations to manage workroom data. All operations follow the pattern: `{"op": "...", "params": {...}}`.

### Available Operations

- **chat**: Send a message to the user
  - `{"op": "chat", "params": {"message": "..."}}`
- **create_task**: Create a new task
  - `{"op": "create_task", "params": {"title": "...", "project_id": "...", "description": "...", "priority": "...", "from_action_id": "..."}}`
  - Duplicate task titles within the same project are rejected with a stock guidance message so the assistant can rename or ask the user for a new title.
- **update_task_status**: Update task status
  - `{"op": "update_task_status", "params": {"task_id": "...", "status": "backlog|doing|done|blocked"}}`
- **link_action_to_task**: Link an action item to a task
  - `{"op": "link_action_to_task", "params": {"action_id": "...", "task_id": "..."}}`
- **update_action_state**: Update action item state
  - `{"op": "update_action_state", "params": {"action_id": "...", "state": "queued|deferred|completed|dismissed|converted_to_task", "defer_until": "...", "added_to_today": true/false}}`
- **delete_project**: Delete one or more projects (soft delete)
  - `{"op": "delete_project", "params": {"project_ids": ["id1", "id2", ...]}}`
  - **Cascade behavior**: Deleting a project also soft-deletes all tasks in that project
  - **Risk level**: High (requires approval in training_wheels mode)
- **delete_task**: Delete one or more tasks (soft delete)
  - `{"op": "delete_task", "params": {"task_ids": ["id1", "id2", ...]}}`
  - **Risk level**: High (requires approval in training_wheels mode)

### Deletion Behavior

- **Soft delete**: Items are marked with `deleted_at` timestamp, not permanently removed
- **Cascade deletion**: Deleting a project automatically soft-deletes all tasks in that project
- **Multiple deletions**: Use a single operation with a list of IDs (e.g., `{"project_ids": ["id1", "id2"]}`)
- **Graceful error handling**: If deletion fails, a chat operation is automatically generated explaining the error to the user

### Trust Levels and Risk

Operations are classified by risk level:
- **Low risk**: `chat` - Always auto-applied
- **Medium risk**: `create_task`, `update_task_status`, `link_action_to_task`, `update_action_state` - Auto-applied in `supervised` and `autonomous` modes
- **High risk**: `delete_project`, `delete_task` - Require approval in `training_wheels` and `supervised` modes, auto-applied in `autonomous` mode

## Fixtures

Deterministic LLM responses are provided via fixtures in `llm_testing/fixtures/llm_ops/`. When `LLM_TESTING_MODE=true`, the LLM service uses these fixtures instead of calling OpenAI.

## Mock Database

When `LLM_TESTING_MODE=true`, tests use an in-memory mock database (`llm_testing/mock_db.py`) instead of connecting to Supabase. This provides:

- **Fast test execution**: No network calls or database setup required
- **Test isolation**: Each scenario starts with a clean state
- **Deterministic behavior**: Consistent test results across runs

### Mock DB Tables

The mock database supports the following tables:

- `users`: User accounts (default test user seeded automatically)
- `projects`: Workroom projects
- `tasks`: Workroom tasks
- `threads`: Chat threads
- `messages`: Thread messages
- `action_items`: Queue action items
- `task_action_links`: Links between tasks and actions
- `task_sources`: Task source metadata

### Seed Endpoints

The `/dev/workroom/seed` and `/dev/queue/seed` endpoints automatically detect `LLM_TESTING_MODE` and populate the mock database instead of the real database. This ensures tests have consistent starting data.

### Mock DB Behavior

- **Filtering**: Supports Supabase-style filters (e.g., `tenant_id=eq.123`)
- **Ordering**: Basic ordering support (asc/desc)
- **Limits**: Respects limit parameters
- **Updates**: PATCH requests update matching rows
- **Response format**: Returns data in the same format as Supabase (lists for multi-row queries, single objects for single-row queries)

## CI Integration

Tests run automatically in CI via `.github/workflows/ci.yml`. The `llm-loop` job runs both legacy scenarios and the new assistant chat & LLM ops scenarios.

### Conditional Execution

The assistant chat & LLM ops e2e tests run conditionally to save time and resources:

- **On PRs**: Only runs when relevant files change:
  - `presentation/api/routes/chat.py`
  - `presentation/api/routes/workroom.py`
  - `presentation/api/routes/queue.py`
  - `presentation/api/routes/dev.py`
  - `services/llm.py`
  - `core/services/llm*.py`
  - `core/domain/llm*.py`
  - `llm_testing/**`
  - `presentation/api/repos/{workroom,queue,tasks,user_settings}.py`
- **On main branch**: Always runs to catch regressions
- **Manual trigger**: Can be triggered via `workflow_dispatch` in `.github/workflows/llm-evals.yml`

## Writing New Scenarios

1. Create a YAML file in `llm_testing/scenarios/`
2. Define steps using the schema above
3. Add snapshot path for regression testing
4. Run the scenario to generate initial snapshot
5. Commit both scenario and snapshot files

## Troubleshooting

- **Snapshot mismatches**: Review the diff in the test output. If the change is intentional, delete the snapshot file and re-run to regenerate.
- **Variable extraction failures**: Ensure the JSONPath in `extract` matches the response structure.
- **LLM_TESTING_MODE not working**: Verify the environment variable is set and fixtures exist for your scenario.
