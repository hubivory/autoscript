#!/usr/bin/env bash
set -e
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
mkdir -p /tmp/fbcli
cd /tmp/fbcli
npm init -y >/dev/null 2>&1 || true
timeout 150 npm install freebuff --no-audit --no-fund 2>&1 | tail -3
echo "=== help ==="
./node_modules/.bin/freebuff --help 2>&1 | head -70 || true
