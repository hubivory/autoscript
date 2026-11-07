#!/usr/bin/env bash
set -e
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
cd "$HOME/mcp-mobile"
npm install --ignore-scripts --no-audit --no-fund
npm run build
echo "--- dist check ---"
ls dist/tools/impl/clients | head
test -f dist/tools/impl/clients/get-loadstring.js && echo "get-loadstring ok"
