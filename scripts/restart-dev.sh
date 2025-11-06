#!/bin/bash
# Restart both the Next.js dev server (port 3001) and FastAPI server (port 8000)

set -e

echo "Restarting dev servers..."

# Kill existing processes on ports 3001 and 8000
if lsof -ti:3001 > /dev/null 2>&1; then
    echo "Killing process(es) on port 3001..."
    kill $(lsof -ti:3001) 2>/dev/null || true
    sleep 1
fi

if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Killing process(es) on port 8000..."
    kill $(lsof -ti:8000) 2>/dev/null || true
    sleep 1
fi

# Start FastAPI server
echo "Starting FastAPI server on port 8000..."
cd "$(dirname "$0")/.."
PYTHONPATH=. uvicorn presentation.api.app:app --reload --port 8000 > /dev/null 2>&1 &
API_PID=$!
echo "FastAPI server started (PID: $API_PID)"

# Start Next.js dev server
echo "Starting Next.js dev server on port 3001..."
cd web
npm run dev > /dev/null 2>&1 &
WEB_PID=$!
echo "Next.js dev server started (PID: $WEB_PID)"

echo ""
echo "Both servers are running:"
echo "  - API: http://localhost:8000 (PID: $API_PID)"
echo "  - Web: http://localhost:3001 (PID: $WEB_PID)"
echo ""
echo "To stop servers, run: kill $API_PID $WEB_PID"

