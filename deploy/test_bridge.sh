#!/usr/bin/env bash
set -e
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
cd "$HOME/mcp-mobile"
if [ -s "$HOME/.mcp_bridge_token" ]; then
  TOKEN=$(cat "$HOME/.mcp_bridge_token")
else
  TOKEN=$(node -e "console.log(require('crypto').randomBytes(24).toString('hex'))")
  umask 077
  printf '%s' "$TOKEN" > "$HOME/.mcp_bridge_token"
fi
if [ -f /tmp/mcp_bridge.pid ] && kill -0 "$(cat /tmp/mcp_bridge.pid)" 2>/dev/null; then
  kill "$(cat /tmp/mcp_bridge.pid)" 2>/dev/null || true
  sleep 1
fi
MCP_AUTH_TOKEN="$TOKEN" nohup node dist/index.js --http > /tmp/mcp_bridge.log 2>&1 &
echo $! > /tmp/mcp_bridge.pid
sleep 6
echo "pid: $(cat /tmp/mcp_bridge.pid)"
echo "--- log ---"
tail -25 /tmp/mcp_bridge.log
echo "--- http root ---"
curl -s -o /dev/null -w "root=%{http_code}\n" http://127.0.0.1:16384/ || true
echo "--- mcp initialize ---"
curl -s -X POST http://127.0.0.1:16384/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}' | head -c 500
echo
