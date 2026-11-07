#!/usr/bin/env bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
cd /tmp/fbcli
if [ -f /tmp/fb_login.pid ] && kill -0 "$(cat /tmp/fb_login.pid)" 2>/dev/null; then
  kill "$(cat /tmp/fb_login.pid)" 2>/dev/null || true
fi
rm -f /tmp/fb_login.log
nohup ./node_modules/.bin/freebuff login > /tmp/fb_login.log 2>&1 < /dev/null &
echo $! > /tmp/fb_login.pid
for i in $(seq 1 15); do
  URL=$(grep -ao 'https://freebuff.com/login?[^[:space:]]*' /tmp/fb_login.log 2>/dev/null | head -1)
  if [ -n "$URL" ]; then break; fi
  sleep 1
done
echo "url=$URL"
echo "pid=$(cat /tmp/fb_login.pid)"
