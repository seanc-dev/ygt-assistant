# Restart Dev Servers

Restart both the Next.js dev server (port 3001) and FastAPI server (port 8000).

## Usage

```bash
./scripts/restart-dev.sh
```

This script will:
1. Kill any existing processes on ports 3001 and 8000
2. Start the FastAPI server on port 8000
3. Start the Next.js dev server on port 3001

Both servers will run in the background. The script will output the PIDs and URLs for both servers.

## Manual Restart

If you prefer to restart manually:

**API Server:**
```bash
PYTHONPATH=. uvicorn presentation.api.app:app --reload --port 8000
```

**Web Server:**
```bash
cd web
npm run dev
```
