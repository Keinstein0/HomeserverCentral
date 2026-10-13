# Post-attach script - runs after VS Code attaches to the container
set -e

echo "=== Attached to Homeserver Central Dev Container ==="

# Verify tools are installed
echo "Checking installed tools..."
command -v docker && echo "✓ Docker CLI"
command -v caddy && echo "✓ Caddy"
command -v go && echo "✓ Go"
command -v python && echo "✓ Python"
command -v node && echo "✓ Node.js"
command -v npm && echo "✓ npm"
command -v git && echo "✓ Git"

# Setup project directory
cd /workspaces/HomeserverCentral

# Install Python dependencies for Auth Service
if [ -f AuthService/requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip install --user -r AuthService/requirements.txt
fi

# Install Node.js dependencies for Homepage
if [ -f Homepage/package.json ]; then
    echo "Installing Node.js dependencies..."
    cd Homepage
    npm install
    cd ..
fi

# Create .env file from example if it doesn't exist
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

echo ""
echo "=== Dev Container Ready ==="
echo ""
echo "Quick start commands:"
echo "  docker compose up -d    # Start all services in background"
echo "  docker compose logs -f  # Watch all service logs"
echo "  docker compose down     # Stop all services"
echo ""
echo "Service URLs:"
echo "  Auth Service: http://localhost:5000/healthz"
echo "  Status API:   http://localhost:5001/healthz"
echo "  Homepage:     http://localhost:5173"
echo "  Caddy:        http://localhost"
echo ""
echo "Edit files in the project directory - all changes are live!"