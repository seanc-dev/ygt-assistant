PY=python

.PHONY: status db-migrate connect-google test-gmail test-calendar ms-connect ms-test-mail ms-test-cal

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


