PY=python

.PHONY: status db-migrate connect-google test-gmail test-calendar ms-connect ms-test-mail ms-test-cal llm-run llm-report llm-record llm-auto-patch

status:
	@echo "Providers:" && echo "  EMAIL=$(PROVIDER_EMAIL) CAL=$(PROVIDER_CAL)" && \
	$(PY) -c "import os; print('DB enabled:', os.getenv('USE_DB','false'))"

db-migrate:
	@SUPABASE_DB_URL=$(SUPABASE_DB_URL) $(PY) scripts/db_migrate.py

connect-google:
	@echo "Open this URL:" && \
	echo "http://localhost:8000/connections/google/oauth/start?user_id=$(USER_ID)"

test-gmail:
	@$(PY) -c "import os; from services.providers.registry import get_email_provider; uid=os.getenv('USER_ID','local-user'); p=get_email_provider(uid); print({'ok': True, 'count': len(p.list_threads('label:inbox',3))})"

test-calendar:
	@$(PY) -c "import os; from datetime import datetime, timedelta, timezone; from services.providers.registry import get_calendar_provider; uid=os.getenv('USER_ID','local-user'); p=get_calendar_provider(uid); now=datetime.now(timezone.utc); print({'ok': True, 'count': len(p.list_events(now.isoformat(), (now+timedelta(days=1)).isoformat()))})"

ms-connect:
	@echo "Open this URL:" && \
	echo "http://localhost:8000/connections/ms/oauth/start?user_id=$(USER_ID)"

ms-test-mail:
	@$(PY) -c "import os; from services.providers.registry import get_email_provider; uid=os.getenv('USER_ID','local-user'); p=get_email_provider(uid); print({'ok': True, 'count': len(p.list_threads('',3))})"

ms-test-cal:
	@$(PY) -c "import os; from datetime import datetime, timedelta, timezone; from services.providers.registry import get_calendar_provider; uid=os.getenv('USER_ID','local-user'); p=get_calendar_provider(uid); now=datetime.now(timezone.utc); print({'ok': True, 'count': len(p.list_events(now.isoformat(), (now+timedelta(days=1)).isoformat()))})"

llm-run:
	@$(PY) llm_testing/runner.py --all

llm-report:
	@echo "Reports in llm_testing/reports"

llm-record:
	@echo "Set RECORD_GRAPH=true and run your flows locally to capture fixtures"

live-smoke:
	@echo "Running live smoke (requires FEATURE_GRAPH_LIVE=true and per-action flags)" && \
	$(PY) scripts/live_smoke.py

llm-auto-patch:
	@RUN_ID=$$(ls -1t llm_testing/reports | head -1); \
	if [ -z "$$RUN_ID" ]; then echo "No run found"; exit 1; fi; \
	$(PY) llm_testing/auto_patch.py $$RUN_ID --dry-run


