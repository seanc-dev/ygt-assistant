PY=python

.PHONY: status db:migrate connect-google test-gmail test-calendar

status:
	@echo "Providers:" && echo "  EMAIL=$(PROVIDER_EMAIL) CAL=$(PROVIDER_CAL)" && \
	$(PY) -c "import os; print('DB enabled:', os.getenv('USE_DB','false'))"

db\:migrate:
	@SUPABASE_DB_URL=$(SUPABASE_DB_URL) $(PY) scripts/db_migrate.py

connect-google:
	@echo "Open this URL:" && \
	echo "http://localhost:8000/connections/google/oauth/start?user_id=$(USER_ID)"

test-gmail:
	@$(PY) - <<'PY'
from services.providers.registry import get_email_provider
prov = get_email_provider("$(USER_ID)")
threads = prov.list_threads("label:inbox", 3)
print({"ok": True, "count": len(threads)})
PY

test-calendar:
	@$(PY) - <<'PY'
from datetime import datetime, timedelta, timezone
from services.providers.registry import get_calendar_provider
prov = get_calendar_provider("$(USER_ID)")
now = datetime.now(timezone.utc)
events = prov.list_events((now).isoformat(), (now+timedelta(days=1)).isoformat())
print({"ok": True, "count": len(events)})
PY


