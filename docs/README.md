# LucidWork docs

LucidWork (working name) is a FastAPI + Next.js workspace focused on Microsoft Graph-first email/calendar flows, a Hub control room, and a Workroom for project/task navigation. Notion OAuth is supported for context; Google connectors are experimental. All envs default to in-memory repos unless `USE_DB=true` enables the Supabase/Postgres layer.

See `docs/CODEBASE_OVERVIEW.md` for architecture and `README.md` for setup.

## Quick start

```bash
python -m pip install -r requirements.txt
PYTHONPATH=. uvicorn presentation.api.app:app --reload --port 8000

cd web
npm install
npm run dev
```

Then open `http://localhost:3001/hub`.

## Tests

```bash
pytest -q
```

## Deploy

- FastAPI backend: Fly.io-ready `Dockerfile` + `fly.toml`
- Web app: Next.js (Pages router) deployable to Vercel or any Node host

---

Internal utilities in `llm_testing/` help exercise LLM-driven flows; they are optional for day-to-day development.
