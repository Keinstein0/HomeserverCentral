# Homeserver Central

A Matrix-powered homeserver with authentication and protected routes.

## Services

### Auth Service
- **Description**: Matrix Auth Gateway for validating room membership
- **Location**: `AuthService/`
- **Type**: Flask application
- **Environment**: See `AuthService/docker-compose.snippet.yml` for details
- **Status**: ✅ Operational

### Status API
- **Description**: API for system status monitoring (not yet implemented)
- **Location**: To be created
- **Type**: Go or Flask application
- **Status**: ❌ Not yet implemented

### Homepage
- **Description**: Svelte/Vite application with live previews
- **Location**: `Homepage/`
- **Current Status**: Static HTML/CSS files
- **Status**: ⚠️ Needs Svelte/Vite setup

### Caddy
- **Description**: Reverse proxy with authentication
- **Location**: `Caddy/Caddyfile`
- **Type**: Caddy web server
- **Status**: ✅ Operational

## Development Setup

### Quick Start (Docker)

1. Set required environment variables:
```bash
cat <<EOF > .env
HOMESERVER_URL=http://tuwunel:8008
BOT_ACCESS_TOKEN=your_bot_token_here
GATEWAY_SECRET_KEY=your_secret_key_here
EOF
```

2. Start services with Docker Compose:
```bash
docker-compose up -d
```

### Quick Start (Local Development)

1. Install dependencies:
```bash
cd AuthService && pip install -r requirements.txt
```

2. Run Auth Service:
```bash
cd AuthService && python app.py
```

3. Start Caddy:
```bash
caddy -config Caddyfile
```

4. Build and run Homepage (when Svelte/Vite project is set up):
```bash
cd Homepage && npm run dev
```

## Development Workflows

### Container Strategy

Based on the project structure, it appears the setup should be:

- **Auth Service**: Minimal container (stable, infrequent changes)
- **Status API**: Minimal container (stable, infrequent changes)  
- **Homepage**: Container with Vite dev server for live previews
- **Caddy**: Container (handles routing and authentication)

### Live Previews

For the Homepage, set up Vite for live previews:
```bash
# In Homepage directory:
npm create vite@latest . -- --template svelte
npm install
snpm run dev
```

### Status API

Create a simple status API service that can be checked:
```bash
# Create Status API directory
mkdir -p StatusAPI

# Add status endpoints (health, info, etc.)
```

## Environment Variables

Required for Auth Service:
- `HOMESERVER_URL`: Matrix homeserver URL
- `BOT_ACCESS_TOKEN`: Bot access token with room access
- `GATEWAY_SECRET_KEY`: Secret for signing session cookies

Optional:
- `SESSION_MAX_AGE`: Session duration in seconds (default: 7 days)
- `MEMBERSHIP_CACHE_TTL`: Cache duration for membership checks (default: 60s)

## Docker Compose Snippet

See `AuthService/docker-compose.snippet.yml` for environment setup:

```yaml
environment:
  HOMESERVER_URL: ${HOMESERVER_URL:-http://tuwunel:8008}
  BOT_ACCESS_TOKEN: ${BOT_ACCESS_TOKEN}
  GATEWAY_SECRET_KEY: ${GATEWAY_SECRET_KEY}
  SESSION_MAX_AGE: 604800
  MEMBERSHIP_CACHE_TTL: 60
```

## Project Notes

- The current Homepage directory only contains static HTML/CSS files
- The status API does not yet exist
- The Caddyfile is already configured to use the auth service
- Authentication is handled through Matrix room membership validation
- The system uses forward_auth for protected routes

## Next Steps

1. **Status API**: Create a simple API for system status
2. **Homepage**: Convert to Svelte/Vite project with live previews
3. **Documentation**: Add API documentation
4. **Testing**: Add health checks and monitoring
5. **Production Setup**: Optimize container configurations