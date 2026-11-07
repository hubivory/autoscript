#!/usr/bin/env bash
set -e
TOKEN=$(cat "$HOME/.mcp_bridge_token")
TUNNEL=$(cat "$HOME/.mcp_tunnel_url" 2>/dev/null || true)
ENV="$HOME/scriptbot/.env"
if [ -n "$TUNNEL" ]; then
  if grep -q '^CONNECT_HOST=' "$ENV"; then
    sed -i "s|^CONNECT_HOST=.*|CONNECT_HOST=$TUNNEL|" "$ENV"
  else
    printf 'CONNECT_HOST=%s\n' "$TUNNEL" >> "$ENV"
  fi
fi
sudo install -m 600 /dev/null /home/ubuntu/.mcp-bridge.env
printf 'MCP_AUTH_TOKEN=%s\n' "$TOKEN" | sudo tee /home/ubuntu/.mcp-bridge.env >/dev/null
sudo chown ubuntu:ubuntu /home/ubuntu/.mcp-bridge.env

sudo install -m 700 /tmp/run_bridge.sh /home/ubuntu/run_bridge.sh
sudo install -m 700 /tmp/run_bot.sh /home/ubuntu/run_bot.sh
sudo install -m 644 /tmp/mcp-bridge.service /etc/systemd/system/mcp-bridge.service
sudo install -m 644 /tmp/scriptbot.service /etc/systemd/system/scriptbot.service
sudo systemctl daemon-reload
sudo systemctl enable mcp-bridge.service >/dev/null
sudo systemctl restart mcp-bridge.service
sleep 4
systemctl is-active mcp-bridge.service
systemctl --no-pager --lines=6 status mcp-bridge.service | tail -8

if grep -q '^DISCORD_TOKEN=.\+' /home/ubuntu/scriptbot/.env; then
  sudo systemctl enable scriptbot.service >/dev/null
  sudo systemctl restart scriptbot.service
  sleep 3
  systemctl is-active scriptbot.service || true
else
  echo "scriptbot: not started (DISCORD_TOKEN empty)"
fi
