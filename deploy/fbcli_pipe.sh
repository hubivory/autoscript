#!/usr/bin/env bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
cd /tmp/fbcli
echo "say OK" | timeout 25 ./node_modules/.bin/freebuff 2>&1 | head -30
echo "exit=$?"
