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

chat-llm-e2e:
	@echo "Running assistant chat & LLM ops e2e scenarios (with fixtures)" && \
	OFFLINE_EVAL=true DEV_MODE=true USE_MOCK_GRAPH=true $(PY) -m llm_testing.runner --scenarios \
		llm_testing/scenarios/assistant_chat_happy_path.yaml \
		llm_testing/scenarios/assistant_chat_edge_cases.yaml \
		llm_testing/scenarios/assistant_chat_live_inbox.yaml \
		llm_testing/scenarios/llm_ops_task_training_wheels.yaml \
		llm_testing/scenarios/llm_ops_task_autonomous.yaml \
		llm_testing/scenarios/llm_ops_queue_focus.yaml \
		llm_testing/scenarios/llm_ops_create_task.yaml \
		llm_testing/scenarios/llm_ops_create_task_duplicate.yaml \
		llm_testing/scenarios/llm_ops_create_task_from_action.yaml \
		llm_testing/scenarios/llm_ops_update_status_all.yaml \
		llm_testing/scenarios/llm_ops_link_action.yaml \
		llm_testing/scenarios/llm_ops_action_state_complete.yaml \
		llm_testing/scenarios/llm_ops_chat.yaml \
		llm_testing/scenarios/llm_ops_defer_deterministic.yaml \
		llm_testing/scenarios/llm_ops_edge_cases.yaml \
		llm_testing/scenarios/llm_ops_delete_project.yaml \
		llm_testing/scenarios/llm_ops_delete_project_multiple.yaml \
		llm_testing/scenarios/llm_ops_delete_project_autonomous.yaml \
		llm_testing/scenarios/llm_ops_delete_task.yaml \
		llm_testing/scenarios/llm_ops_delete_task_multiple.yaml \
		llm_testing/scenarios/llm_ops_delete_task_autonomous.yaml \
		llm_testing/scenarios/llm_ops_delete_error_handling.yaml

chat-llm-e2e-live:
	@echo "Running assistant chat & LLM ops e2e scenarios (with LIVE LLM calls)" && \
	echo "⚠️  This will make real API calls and incur costs. Requires OPENAI_API_KEY." && \
	OFFLINE_EVAL=true DEV_MODE=true USE_MOCK_GRAPH=true LLM_TESTING_MODE=false $(PY) -m llm_testing.runner --scenarios \
		llm_testing/scenarios/assistant_chat_happy_path.yaml \
		llm_testing/scenarios/assistant_chat_edge_cases.yaml \
		llm_testing/scenarios/assistant_chat_live_inbox.yaml \
		llm_testing/scenarios/llm_ops_task_training_wheels.yaml \
		llm_testing/scenarios/llm_ops_task_autonomous.yaml \
		llm_testing/scenarios/llm_ops_queue_focus.yaml \
		llm_testing/scenarios/llm_ops_create_task.yaml \
		llm_testing/scenarios/llm_ops_create_task_duplicate.yaml \
		llm_testing/scenarios/llm_ops_create_task_from_action.yaml \
		llm_testing/scenarios/llm_ops_update_status_all.yaml \
		llm_testing/scenarios/llm_ops_link_action.yaml \
		llm_testing/scenarios/llm_ops_action_state_complete.yaml \
		llm_testing/scenarios/llm_ops_chat.yaml \
		llm_testing/scenarios/llm_ops_defer_deterministic.yaml \
		llm_testing/scenarios/llm_ops_edge_cases.yaml \
		llm_testing/scenarios/llm_ops_delete_project.yaml \
		llm_testing/scenarios/llm_ops_delete_project_multiple.yaml \
		llm_testing/scenarios/llm_ops_delete_project_autonomous.yaml \
		llm_testing/scenarios/llm_ops_delete_task.yaml \
		llm_testing/scenarios/llm_ops_delete_task_multiple.yaml \
		llm_testing/scenarios/llm_ops_delete_task_autonomous.yaml \
		llm_testing/scenarios/llm_ops_delete_error_handling.yaml

llm-report:
	@echo "Reports in llm_testing/reports"

llm-record:
	@echo "Set RECORD_GRAPH=true and run your flows locally to capture fixtures"

live-smoke:
	@echo "Running live smoke (requires FEATURE_GRAPH_LIVE=true and per-action flags)" && \
	$(PY) scripts/live_smoke.py

live-on:
	@echo "Enabling FEATURE_GRAPH_LIVE in .env.dev" && \
	grep -q '^FEATURE_GRAPH_LIVE=' .env.dev 2>/dev/null && \
	sed -i '' 's/^FEATURE_GRAPH_LIVE=.*/FEATURE_GRAPH_LIVE=true/' .env.dev || \
	echo 'FEATURE_GRAPH_LIVE=true' >> .env.dev

live-off:
	@echo "Disabling FEATURE_GRAPH_LIVE in .env.dev" && \
	grep -q '^FEATURE_GRAPH_LIVE=' .env.dev 2>/dev/null && \
	sed -i '' 's/^FEATURE_GRAPH_LIVE=.*/FEATURE_GRAPH_LIVE=false/' .env.dev || \
	echo 'FEATURE_GRAPH_LIVE=false' >> .env.dev

llm-auto-patch:
	@RUN_ID=$$(ls -1t llm_testing/reports | head -1); \
	if [ -z "$$RUN_ID" ]; then echo "No run found"; exit 1; fi; \
	$(PY) llm_testing/auto_patch.py $$RUN_ID --dry-run


