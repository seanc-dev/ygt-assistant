#!/bin/bash
# Quick deployment script for lucid-work

set -e

echo "🚀 Deploying lucid-work..."

# Deploy backend to Fly.io
echo "📦 Deploying backend to Fly.io..."
cd "$(dirname "$0")/.."
flyctl deploy --app lucid-work --remote-only

# Get backend URL
BACKEND_URL="https://lucid-work.fly.dev"
echo "✅ Backend deployed to: $BACKEND_URL"

# Deploy frontend to Vercel
echo "🌐 Deploying frontend to Vercel..."
cd web

# Set environment variable if not set
if ! vercel env ls | grep -q "NEXT_PUBLIC_ADMIN_API_BASE"; then
    echo "Setting NEXT_PUBLIC_ADMIN_API_BASE..."
    echo "$BACKEND_URL" | vercel env add NEXT_PUBLIC_ADMIN_API_BASE production
fi

# Deploy
vercel --prod

echo "✅ Deployment complete!"
echo "Backend: $BACKEND_URL"
echo "Frontend: Check Vercel dashboard for URL"

