#!/bin/sh
set -x
exec > /tmp/mcp-server.log 2>&1

echo "=== mcp-start.sh running at $(date) ==="

pkill -f 'mcp-proxy' 2>/dev/null
pkill -f 'mcp-language-server' 2>/dev/null
pkill -f 'server-filesystem' 2>/dev/null
sleep 1

NODE_BIN="/usr/local/share/nvm/versions/node/v24.20.0/bin"
export PATH="$NODE_BIN:$PATH"

# --- Python language server (AuthService) on port 3001 ---
nohup "$NODE_BIN/npx" -y mcp-proxy --host 127.0.0.1 --port 3001 -- \
  /go/bin/mcp-language-server --workspace /workspaces/HomeserverCentral/AuthService --lsp pylsp &
disown
echo "python LS started on 3001, pid $!"

sleep 1

# --- TypeScript/JS language server (Homepage) on port 3002 ---
nohup "$NODE_BIN/npx" -y mcp-proxy --host 127.0.0.1 --port 3002 -- \
  /go/bin/mcp-language-server --workspace /workspaces/HomeserverCentral/Homepage --lsp typescript-language-server -- --stdio &
disown
echo "typescript LS started on 3002, pid $!"

sleep 1

# --- Generic read-only filesystem access, whole repo, port 3003 ---
nohup "$NODE_BIN/npx" -y mcp-proxy --host 127.0.0.1 --port 3003 -- \
  npx -y @modelcontextprotocol/server-filesystem /workspaces/HomeserverCentral &
disown
echo "filesystem server started on 3003, pid $!"