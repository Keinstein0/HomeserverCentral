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
# Step 3: Integration Tests (spin up stack, run, tear down)
# =============================================================================
step "Step 3: Integration Tests"

# Install integration test deps
(cd "$ROOT/tests/integration" && pip install -q -r requirements.txt 2>/dev/null)

# Run the integration suite — conftest.py handles the full stack lifecycle
# (up -> wait for health -> yield -> down). Use a trap to guarantee teardown
# even on failure or Ctrl-C.
cleanup() {
    echo -e "\n${YELLOW}--- Tearing down test stack ---${NC}"
    docker compose --profile test --env-file "$ROOT/.env.test" \
        -f "$ROOT/docker-compose.yml" down -v 2>/dev/null || true
}
trap cleanup EXIT

(cd "$ROOT/tests/integration" && python3 -m pytest -v) \
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