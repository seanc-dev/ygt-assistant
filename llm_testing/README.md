## LLM Testing Harness

The `llm_testing` package drives end-to-end assistant scenarios against the
FastAPI in-process backend.  Each scenario issues real HTTP requests, validates
responses via JSONPath / substring expectations, and (optionally) snapshots the
operations payload returned by `/assistant-suggest`.

### Testing Structure

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

### Running scenarios

```bash
python -m llm_testing.runner --scenarios llm_testing/scenarios/llm_ops_create_task.yaml
```

Use `--all` to execute every scenario, or pass multiple paths in `--scenarios`.

### Live LLM mode

By default, scenarios use deterministic fixtures (`LLM_TESTING_MODE=true`).  To
exercise the current LLM provider end-to-end, pass `--live` (or set
`LLM_TESTING_MODE=false`) when running the runner:

```bash
OPENAI_API_KEY=... python -m llm_testing.runner --scenarios ... --live
```

**Snapshot behavior:**
- **Full transcript snapshots**: Only enforced with fixtures (infrastructure testing)
- **Operation snapshots**: Only enforced with fixtures (deterministic operation structure)
- **Live LLM mode**: Snapshots generate warnings but don't fail tests (expected variance)

The same HTTP flow and executor logic runs in both modes, so failures surface as 4xx/5xx or failed assertions.

### Scenario tips

- Use `extract` blocks plus `__var__` in later requests to reuse IDs.
- Expectations support `<var>` substitution inside `contains`/`jsonpath` strings.
- Prefer precise `jsonpath` assertions (e.g. `"result.ok": true`) so regressions
  fail immediately instead of relying on text search.

