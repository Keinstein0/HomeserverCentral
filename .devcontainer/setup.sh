# Dev Container Setup Script
# This script sets up the development environment after container creation
set -e

# Install Caddy Web Server (for dev testing outside containers)
echo "Installing Caddy..."
curl -1sLf 'https://pkgs.caddy.dev/DEBIAN.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-archive-keyring.gpg 2>/dev/null || true
echo "deb [signed-by=/usr/share/keyrings/caddy-archive-keyring.gpg] https://pkgs.caddy.dev/debian/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/caddy.list > /dev/null
sudo apt-get update
sudo apt-get install -y caddy tree htop dnsutils net-tools

# Setup project directory
cd /workspaces/HomeserverCentral

# Install Python dependencies for Auth Service
if [ -f AuthService/requirements.txt ]; then
    echo "Installing Python dependencies for Auth Service..."
    pip install --user -r AuthService/requirements.txt
fi

# Install Node.js dependencies for Homepage
if [ -f Homepage/package.json ]; then
    echo "Installing Node.js dependencies for Homepage..."
    cd Homepage
    npm install
    cd ..
fi

# Create .env file from example if it doesn't exist
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example - please edit with your actual values"
fi

# Create necessary directories for Docker volumes
mkdir -p /tmp/homeserver-central

echo "=== Dev Container Setup Complete ==="