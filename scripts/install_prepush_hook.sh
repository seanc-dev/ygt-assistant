#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -z "$ROOT_DIR" ]; then
  echo "Not inside a git repository. Aborting." >&2
  exit 1
fi

HOOK_DIR="$ROOT_DIR/.git/hooks"
HOOK_FILE="$HOOK_DIR/pre-push"

mkdir -p "$HOOK_DIR"
cat > "$HOOK_FILE" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
cd "$ROOT_DIR"

# If GitHub CLI is not available or not authenticated, skip silently
if ! command -v gh >/dev/null 2>&1; then
  exit 0
fi

# Sync GitHub Actions secrets from local .env files (if present)
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/sync_gh_secrets.py || true
fi
HOOK

chmod +x "$HOOK_FILE"
echo "Installed pre-push hook to sync GH Actions secrets from .env/.env.local"

