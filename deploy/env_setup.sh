#!/usr/bin/env bash
set -e
TOKEN=$(cat "$HOME/.mcp_bridge_token")
ENV="$HOME/scriptbot/.env"
if [ ! -f "$ENV" ]; then
  cat > "$ENV" <<EOF
DISCORD_TOKEN=
GUILD_IDS=
COMMAND_PREFIX=!
MCP_URL=http://127.0.0.1:16384/mcp
MCP_AUTH_TOKEN=$TOKEN
PERPLEXITY_API_KEY=
PERPLEXITY_MODEL=sonar-pro
FALLBACK_API_KEY=
FALLBACK_MODEL=
FALLBACK_URL=
MAX_CONTEXT_CHARS=60000
REQUEST_TIMEOUT=180
EOF
else
  if grep -q '^MCP_AUTH_TOKEN=' "$ENV"; then
    sed -i "s|^MCP_AUTH_TOKEN=.*|MCP_AUTH_TOKEN=$TOKEN|" "$ENV"
  else
    printf 'MCP_AUTH_TOKEN=%s\n' "$TOKEN" >> "$ENV"
  fi
  grep -q '^MCP_URL=' "$ENV" || printf 'MCP_URL=http://127.0.0.1:16384/mcp\n' >> "$ENV"
fi
chmod 600 "$ENV"
echo "env ready at $ENV"
