#!/usr/bin/env bash
set -e
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
cd "$HOME/mcp-mobile"
npm install --omit=dev --ignore-scripts --no-audit --no-fund
node -v
npm -v
node --input-type=module -e "import('@modelcontextprotocol/sdk/server/index.js').then(()=>console.log('sdk ok')).catch(e=>{console.error('sdk fail',e.message);process.exit(1)})"
