#!/usr/bin/env bash
set -e
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 20 >/dev/null
npm install -g freebuff --no-audit --no-fund 2>&1 | tail -2
which freebuff
freebuff --version 2>&1 | head -2 || true
mkdir -p "$HOME/scriptbot/.fbcli_work"
chmod 700 "$HOME/scriptbot/.fbcli_work"
