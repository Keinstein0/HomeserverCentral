#!/usr/bin/env bash
# =============================================================================
# Local CI Pipeline — mirrors the GitHub Actions workflow (.github/workflows/ci.yml)
# so developers can run the exact same 4-step sequence locally without pushing.
#
# Prerequisites: Go, Python 3, Node.js, Docker + Docker Compose installed.
#
# Usage:  bash scripts/ci.sh
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

step() {
    echo -e "\n${YELLOW}=== $1 ===${NC}\n"
}

ok() {
    echo -e "${GREEN}✓ $1${NC}"
}

fail() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# =============================================================================
# Step 1: Lint & Static Analysis
# =============================================================================
step "Step 1: Lint & Static Analysis"

# --- Status API (Go) ---
if command -v golangci-lint &>/dev/null; then
    (cd "$ROOT/StatusAPI" && golangci-lint run --config .golangci.yml ./...) \
        && ok "golangci-lint (Status API)" || fail "golangci-lint (Status API)"
else
    echo "  golangci-lint not found — skipping Go lint (install: go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest)"
fi

# --- Auth Service (Python) ---
if command -v flake8 &>/dev/null; then
    (cd "$ROOT/AuthService" && flake8 app.py tests/) \
        && ok "flake8 (Auth Service)" || fail "flake8 (Auth Service)"
else
    echo "  flake8 not found — skipping (install: pip install flake8)"
fi

if command -v black &>/dev/null; then
    (cd "$ROOT/AuthService" && black --check app.py tests/) \
        && ok "black --check (Auth Service)" || fail "black --check (Auth Service)"
else
    echo "  black not found — skipping (install: pip install black)"
fi

# --- Homepage (SvelteKit) ---
(cd "$ROOT/Homepage" && npm run check) \
    && ok "svelte-check (Homepage)" || fail "svelte-check (Homepage)"

# =============================================================================
# Step 2: Unit Tests
# =============================================================================
step "Step 2: Unit Tests"

# --- Status API (Go) ---
(cd "$ROOT/StatusAPI" && go test -v -race ./...) \
    && ok "Go unit tests (Status API)" || fail "Go unit tests (Status API)"

# --- Auth Service (Python) ---
(cd "$ROOT/AuthService" && pip install -q -r requirements-dev.txt 2>/dev/null; \
    python3 -m pytest -v tests/) \
    && ok "Python unit tests (Auth Service)" || fail "Python unit tests (Auth Service)"

# --- Homepage (SvelteKit) ---
(cd "$ROOT/Homepage" && npm run build && npm run test) \
    && ok "Homepage build + unit tests" || fail "Homepage build + unit tests"

# =============================================================================
# Step 3: Integration Tests (spin up stack, run in-network, tear down)
# =============================================================================
step "Step 3: Integration Tests"

# Consistent project name so the host and the in-network test-runner
# (which shells out to `docker compose` for INT-CMP-01/02) address the
# same compose project.
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-homeserver}"

# Use a trap to guarantee teardown even on failure or Ctrl-C.
cleanup() {
    echo -e "\n${YELLOW}--- Tearing down test stack ---${NC}"
    docker compose --profile test --env-file "$ROOT/.env.test" \
        -f "$ROOT/docker-compose.yml" down -v 2>/dev/null || true
}
trap cleanup EXIT

# Spin up the full test stack (builds images, starts all services).
docker compose --profile test --env-file "$ROOT/.env.test" \
    -f "$ROOT/docker-compose.yml" up -d --build \
    && ok "Test stack up" || fail "Test stack up"

# Run the integration suite INSIDE the compose network via the test-runner
# service: the production hostnames resolve to the local Caddy container
# through Docker DNS aliases (see docker-compose.yml), so the suite
# exercises the exact production virtual hosts. The runner lives on its own
# `runner` profile so `up` never auto-starts it (a premature up-started
# suite would race this one and corrupt the shared Status API cache /
# mock state -> flaky INT-STA-03/04/05).
docker compose --profile test --profile runner --env-file "$ROOT/.env.test" \
    -f "$ROOT/docker-compose.yml" run --rm test-runner \
    && ok "Integration tests" || fail "Integration tests"

# =============================================================================
# Step 4: Cleanup (handled by the trap above + conftest.py teardown)
# =============================================================================
step "Step 4: Cleanup"
# The trap already ran `docker compose down -v`. Confirm it's clean.
echo "  Test stack torn down successfully."

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All CI steps passed! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"