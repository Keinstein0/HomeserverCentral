#!/bin/bash
# Dev Container Setup Script
set -e

# Install CLI Utilities first
echo "Installing utilities..."
sudo apt-get update && sudo apt-get install -y tree htop dnsutils net-tools

# Safely attempt to add Caddy repository
echo "Setting up Caddy repository..."
curl -1sLf 'https://pkgs.caddy.dev/DEBIAN.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-archive-keyring.gpg 2>/dev/null || true
echo "deb [signed-by=/usr/share/keyrings/caddy-archive-keyring.gpg] https://pkgs.caddy.dev/debian/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/caddy.list > /dev/null

# Try installing Caddy, but don't fail the entire setup if network/TLS drops
sudo apt-get update || true
sudo apt-get install -y caddy || echo "WARNING: Caddy installation failed, skipping for now."

# -------------------------------------------------------------
# Install Language Servers for mcp-language-server
# -------------------------------------------------------------
echo "Installing Language Servers..."
sudo npm install -g typescript typescript-language-server svelte-language-server pyright || true

# Ensure Go binaries (gopls, mcp-language-server) are in PATH
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
export PATH="$PATH:$HOME/go/bin"
# -------------------------------------------------------------

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
    echo "Created .env from .env.example"
fi

# Create necessary directories
mkdir -p /tmp/homeserver-central

echo "=== Dev Container Setup Complete ==="