#!/bin/bash
# Script to seed dev data for local development

API_BASE="${API_BASE:-http://localhost:8000}"
USER_ID="${USER_ID:-dev-user}"

echo "🌱 Seeding dev data..."
echo "API: $API_BASE"
echo "User ID: $USER_ID"
echo ""

# Seed queue
echo "📦 Seeding queue..."
QUEUE_RESULT=$(curl -s -X POST "$API_BASE/dev/queue/seed?count=10" \
  -H "Cookie: user_id=$USER_ID" \
  -H "Content-Type: application/json")

echo "$QUEUE_RESULT" | python3 -m json.tool 2>/dev/null || echo "$QUEUE_RESULT"
echo ""

# Seed schedule
echo "📅 Seeding schedule..."
SCHEDULE_RESULT=$(curl -s -X POST "$API_BASE/dev/schedule/seed" \
  -H "Cookie: user_id=$USER_ID" \
  -H "Content-Type: application/json")

echo "$SCHEDULE_RESULT" | python3 -m json.tool 2>/dev/null || echo "$SCHEDULE_RESULT"
echo ""

# Verify
echo "✅ Verifying data..."
QUEUE_CHECK=$(curl -s "$API_BASE/api/queue?limit=5" -H "Cookie: user_id=$USER_ID")
TOTAL=$(echo "$QUEUE_CHECK" | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('total', 0))" 2>/dev/null || echo "0")

echo "Queue has $TOTAL total items"
echo ""
echo "🎉 Done! Visit http://localhost:3001/hub to see the data"

