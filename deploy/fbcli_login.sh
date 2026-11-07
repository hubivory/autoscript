#!/usr/bin/env bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
cd /tmp/fbcli
printf '\n' | timeout 40 ./node_modules/.bin/freebuff login 2>&1 | tr -d '\000' | strings | head -40
echo "exit=$?"
