#!/bin/bash
# Restart the Next.js dev server on port 3001

set -e

echo "Stopping existing dev server..."

# Kill processes by port
if lsof -ti:3001 > /dev/null 2>&1; then
  echo "Found process on port 3001, killing..."
  lsof -ti:3001 | xargs kill -9 2>/dev/null || true
fi

# Kill processes by name pattern
pkill -f "next dev" 2>/dev/null || true

# Wait for processes to fully terminate
sleep 2

echo "Starting dev server in web/ directory..."

# Change to web directory and start server
cd "$(dirname "$0")/../web" || exit 1
npm run dev > /tmp/dev-server.log 2>&1 &
DEV_PID=$!

echo "Dev server starting (PID: $DEV_PID)..."
echo "Logs: /tmp/dev-server.log"

# Wait for server to start
sleep 5

# Verify server is running
if lsof -ti:3001 > /dev/null 2>&1; then
  echo "✅ Dev server is running on port 3001"
  echo "   URL: http://localhost:3001"
else
  echo "❌ Dev server failed to start"
  echo "   Check logs: tail -f /tmp/dev-server.log"
  exit 1
fi

