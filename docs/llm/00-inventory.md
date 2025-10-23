# LLM Evals Inventory (Microsoft-first)

- Backend: FastAPI in `presentation/api/`; providers selected via `services.providers.registry`.
- Providers: Microsoft Graph at `services/microsoft_email.py`, `services/microsoft_calendar.py`.
- Seams: `services/gmail.py`, `services/calendar.py` delegate to registry.
- Testing infra present: `llm_testing/backends/{inprocess,http}.py`, evaluation modules.
- CI: `.github/workflows/ci.yml` exists; will add `llm-evals.yml` for LLM evals.
- Env vars: need `USE_MOCK_GRAPH`, `RECORD_GRAPH`, `LLM_EVAL_MODEL`, `LLM_EVAL_API_KEY`, `MAX_REGRESSION`, `OFFLINE_EVAL`.
- Mock injection point: either registry env switch or `presentation/api/deps/providers.py`.
- Redaction: no message bodies or tokens in logs; use `utils/metrics.py` counters only.
