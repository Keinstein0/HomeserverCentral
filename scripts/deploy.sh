#!/usr/bin/env bash
# =============================================================================
# deploy.sh - HomeserverCentral Continuous Deployment Runner
# =============================================================================
# Idempotent host-side deployment script. Pulls latest repo configs, pulls
# published container images from GHCR, recreates updated services, and
# applies zero-downtime reloads to Caddy.
#
# Usage:
#   ./scripts/deploy.sh [BRANCH]
#
# Default branch is 'main' (or the currently checked out branch).
# =============================================================================
set -euo pipefail

LOCK_FILE="/tmp/homeserver-deploy.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "==> Another deployment is already in progress. Exiting cleanly."
    exit 0
fi

# Ensure we run from repository root regardless of where script is called
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

COMPOSE_FILE="docker-compose.prod.yml"
TARGET_BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

# Fallback if in detached HEAD
if [ "${TARGET_BRANCH}" = "HEAD" ]; then
    TARGET_BRANCH="main"
fi

echo "============================================================"
echo "==> Deploying HomeserverCentral on branch: ${TARGET_BRANCH}"
echo "==> Working directory: ${REPO_DIR}"
echo "==> Compose file:      ${COMPOSE_FILE}"
echo "============================================================"

# 1. Update repository configs (Caddyfile, docker-compose.prod.yml, etc.)
echo "==> [1/4] Pulling latest git repository changes..."
git fetch origin "${TARGET_BRANCH}"
git checkout "${TARGET_BRANCH}"
git pull --ff-only origin "${TARGET_BRANCH}"

# 2. Pull pre-built images from GitHub Container Registry (GHCR)
echo "==> [2/4] Pulling updated container images from GHCR..."
docker compose -f "${COMPOSE_FILE}" pull

# 3. Recreate only updated containers
# Caddy is untouched if its image did not change; application services recreate cleanly
echo "==> [3/4] Recreating updated application containers..."
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

# 4. Zero-downtime hot-reload of Caddy in case Caddyfile changed
echo "==> [4/4] Reloading Caddy configuration (0ms downtime)..."
if docker compose -f "${COMPOSE_FILE}" ps --status running --format '{{.Service}}' | grep -q "^caddy$"; then
    docker compose -f "${COMPOSE_FILE}" exec -T caddy caddy reload --config /etc/caddy/Caddyfile
    echo "==> Caddy reloaded successfully."
else
    echo "==> Note: Caddy was not running; it has been started by docker compose up."
fi

echo "============================================================"
echo "==> Deployment completed successfully at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"
