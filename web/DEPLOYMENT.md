# Vercel Deployment Configuration

## Environment Variables for Vercel

Set these in your Vercel project settings (or via CLI):

```bash
NEXT_PUBLIC_ADMIN_API_BASE=https://lucid-work.fly.dev
```

## Fly.io Backend URL

- Backend URL: `https://lucid-work.fly.dev`
- Health check: `https://lucid-work.fly.dev/health`

## Deployment Steps

1. **Link Vercel project** (run from web/ directory):

   ```bash
   cd web
   vercel link
   # Or create new project:
   vercel
   ```

2. **Set environment variables**:

   ```bash
   vercel env add NEXT_PUBLIC_ADMIN_API_BASE production
   # Enter: https://lucid-work.fly.dev
   ```

3. **Deploy**:
   ```bash
   vercel --prod
   ```

## Project Structure

- Frontend: `/web` directory (Next.js)
- Backend: Root directory (FastAPI, deployed to Fly.io)
- Backend configured with DEV_MODE=true for dummy data
