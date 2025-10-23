# LLM-first Testing Architecture (Microsoft-first)

## Components
- Scenario YAMLs define goal, inputs, expectations, rubric, thresholds.
- Harness runs backend in mock mode (USE_MOCK_GRAPH=true), applies fixtures, calls endpoints, records transcripts.
- Evaluator LLM (OpenAI) grades; offline regex fallback when no key.
- Metrics aggregator gates CI on regressions; reporters emit Markdown and JUnit.
- Optional record/replay adapter for local fixture capture.

## Flow
1. Runner loads scenarios → for each:
   - Set env, load fixtures into mock providers.
   - Execute endpoint calls per flow (plan, triage, approve/send, undo, token-expired).
   - Save transcripts to `llm_testing/reports/<run_id>/<scenario>.json`.
2. Evaluator computes per-criterion scores (0..1) + rationale.
3. Metrics compares to baseline, enforces thresholds.

## Determinism
- Mock providers return data from JSON fixtures.
- Offline evaluator uses regex must/must_not checks.
- No network calls to Microsoft in CI; OpenAI optional.
