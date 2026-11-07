#!/usr/bin/env bash
set -e
ARCH=$(uname -m)
case "$ARCH" in
  aarch64|arm64) CF=cloudflared-linux-arm64 ;;
  x86_64|amd64) CF=cloudflared-linux-amd64 ;;
  *) echo "unsupported arch $ARCH"; exit 1 ;;
esac
if [ ! -x "$HOME/cloudflared" ]; then
  curl -fsSL -o "$HOME/cloudflared" "https://github.com/cloudflare/cloudflared/releases/latest/download/$CF"
  chmod +x "$HOME/cloudflared"
fi
if [ -f /tmp/cloudflared.pid ] && kill -0 "$(cat /tmp/cloudflared.pid)" 2>/dev/null; then
  kill "$(cat /tmp/cloudflared.pid)" 2>/dev/null || true
  sleep 1
fi
nohup "$HOME/cloudflared" tunnel --url http://localhost:16384 --no-autoupdate > /tmp/cloudflared.log 2>&1 &
echo $! > /tmp/cloudflared.pid
for i in $(seq 1 20); do
  URL=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -1 || true)
  if [ -n "$URL" ]; then break; fi
  sleep 1
done
echo "url: $URL"
echo "$URL" > "$HOME/.mcp_tunnel_url"
echo "--- log tail ---"
tail -8 /tmp/cloudflared.log
