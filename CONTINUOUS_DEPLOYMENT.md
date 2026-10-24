# Continuous Deployment Architecture & Roadmap

This document outlines the architecture, security model, and implementation roadmap for Continuous Deployment (CD) to the homeserver.

---

## 1. High-Level Concept

The deployment pipeline is built around an **asymmetric hybrid model**:
* **Heavy work happens on GitHub Actions:** Linting, automated testing, asset compilation, and Docker image builds are performed in GitHub's cloud environment to conserve homeserver CPU and RAM.
* **Minimal work happens on the homeserver:** The homeserver (an 8 GB RAM gateway/router machine) only pulls pre-built container images and static configs, keeping local resource usage and deployment latency minimal.
* **Super Caddy stays online:** Caddy manages ingress for the Matrix server, other physical LAN machines, and central services. It remains continuously running to prevent dropping connections or tearing down TLS tunnels.

---

## 2. Selected Architecture: Micro-Frontend Hybrid

Rather than baking static files into Caddy (which forces a gateway restart) or moving loose files over the filesystem (which creates state and sync complexity), we adopt a micro-container approach:

1. **`caddy` (Super Reverse Proxy):**
   - Continuously running front door.
   - Terminates TLS, proxies to Matrix, external hosts, and local services.
   - Applies zero-downtime hot-reloads (`caddy reload`) only when route configurations change.

2. **`homepage` (Lightweight Frontend Container):**
   - Packaged as a dedicated, ultra-minimal web server (e.g., `nginx:alpine` or `caddy:alpine`) serving the compiled Svelte static assets.
   - Runs with an extremely small memory footprint (~5–8 MB RAM).
   - Can be restarted independently in less than a second without touching the main Caddy proxy.

3. **`matrix-auth-gateway` & `status-api`:**
   - Standard containerized backend services pushed to and pulled from GitHub Container Registry (GHCR).

---

## 3. Security & Webhook Model

Because SSH and VPN tunnels are prohibited by network policy, the deployment trigger is an inbound HTTPS webhook call hardened with defense-in-depth:

1. **No Static Passwords (GitHub OIDC Cryptographic Attestation):**
   - GitHub Actions requests a short-lived OIDC JWT signed by GitHub (`token.actions.githubusercontent.com`).
   - The token contains cryptographically verified claims: repository name, workflow branch (`refs/heads/main`), and actor.
   - The webhook receiver verifies the token against GitHub's public JSON Web Key Sets (JWKS).
   - *Alternative/Fallback:* HMAC-SHA256 signature (`X-Hub-Signature-256`) with a 64-character high-entropy secret.

2. **Zero Command Injection (Static Action):**
   - The webhook endpoint accepts no execution arguments or commands from the network.
   - Any valid incoming trigger executes one predefined, static shell script on the host filesystem.

3. **Network & Proxy Hardening in Caddy:**
   - Obscure, unguessable webhook route path.
   - IP restriction limiting webhook calls to GitHub's public runner IP ranges (published at GitHub's meta API).
   - Strict rate-limiting (e.g., maximum 2 triggers per minute) to eliminate spam or brute-force attempts.

---

## 4. End-to-End Workflow

```
[ Developer ]
      │
      │ git push origin main
      ▼
┌────────────────────────────────────────────────────────┐
│ GitHub Actions                                         │
│  ├─ 1. Run lint and test suites (existing CI)          │
│  ├─ 2. Build Svelte static files                       │
│  ├─ 3. Build & push Docker images to GHCR:             │
│  │     • matrix-auth-gateway                           │
│  │     • status-api                                    │
│  │     • homepage (static container)                   │
│  ├─ 4. Request short-lived GitHub OIDC JWT             │
│  └─ 5. POST to homeserver webhook endpoint with JWT   │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ HTTPS POST /<obscure-webhook-endpoint>
                            ▼
┌────────────────────────────────────────────────────────┐
│ Homeserver: Super Caddy Ingress                        │
│  ├─ Verifies IP source (GitHub runner ranges)         │
│  ├─ Applies rate limiting                             │
│  └─ Reverse-proxies request to Webhook Runner          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Homeserver: Webhook Runner (e.g. adnanh/webhook)       │
│  ├─ Validates JWT signature, repo, and branch claims   │
│  └─ Executes local static deploy script               │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Homeserver: Local Deploy Script Execution              │
│  ├─ 1. git pull origin main (updates configs/Caddyfile)│
│  ├─ 2. docker compose pull matrix-auth-gateway         │
│  │                         status-api homepage         │
│  ├─ 3. docker compose up -d matrix-auth-gateway        │
│  │                          status-api homepage        │
│  └─ 4. If Caddyfile modified: caddy reload             │
│        (0 ms downtime, no dropped Matrix connections)  │
└────────────────────────────────────────────────────────┘
```

---

## 5. Roadmap & Tasks to Complete

### Phase 1: Container & Build Preparations
- [x] **Frontend Production Dockerfile**: Create a minimal production Dockerfile for `Homepage` (e.g. `nginx:alpine` or minimal Caddy) that serves static files built from SvelteKit.
- [x] **GHCR Publishing Pipeline**: Extend GitHub Actions to build and push container images (`homepage`, `status-api`, `matrix-auth-gateway`) to GitHub Container Registry on pushes to `main`.
- [x] **Production Compose Definition**: Create the compose setup (docker-compose.prod.yml) with image references pointing to GHCR rather than local dev build contexts.

### Phase 2: Webhook Runner & Host Hardening
- [ ] **Webhook Receiver Setup**: Install and configure a lightweight webhook daemon on the homeserver (e.g. `adnanh/webhook` or a small daemon) running under an unprivileged user with Docker permissions.
- [ ] **OIDC / Signature Validation Rule**: Configure the webhook receiver to validate GitHub OIDC tokens (or HMAC-SHA256 signatures) ensuring only commits to `main` from the authorized repository are accepted.
- [ ] **Host Deploy Script**: Create the idempotent host script (`deploy.sh`) responsible for running `git pull`, `docker compose pull`, `docker compose up -d`, and `caddy reload`.

### Phase 3: Ingress & Caddy Routing
- [ ] **Webhook Route Definition**: Add an obscure, reverse-proxied route in Caddy directing external webhook requests to the local webhook daemon.
- [ ] **Access Restrictions**: Apply Caddy filters (GitHub IP range checks and rate-limiting rules) to protect the webhook route.
- [X] **Internal Routing Update**: Route the frontend domain in Caddy to the new `homepage` container.

### Phase 4: CI/CD Wiring & Verification
- [ ] **CD Trigger Job in GitHub Actions**: Add a deployment step to GitHub Actions that requests the OIDC token and sends the webhook payload once all builds and tests pass.
- [ ] **Dry Run & Verification**: Perform an end-to-end test on `main` to verify the automated update process and confirm zero disruption to active Matrix traffic.
