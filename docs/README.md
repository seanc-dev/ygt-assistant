# CoachFlow

CoachFlow integrates Notion, email, and calendars with an LLM-assisted workflow to propose triage actions you can approve via the admin portal. It uses Nylas for email/calendar, Notion API for data, Postmark for email, and OpenAI for LLM features. The API is FastAPI on Fly.io; the site is Next.js on Vercel.

For detailed architecture, see `docs/CODEBASE_OVERVIEW.md`.

## Quick Start

```bash
git clone https://github.com/seanc-dev/coach-flow-app.git
cd coach-flow-app
pip install -r requirements.txt
cp env.production.sample .env
# Fill in secrets
uvicorn presentation.api.app:app --reload
```

## Tests

```bash
pytest -q
```

## Deploy

- Fly app: `coach-flow-app`
- `flyctl deploy`

---

The remainder of this document refers to internal testing utilities in `llm_testing/`. These tools are optional and not required for production.
