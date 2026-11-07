#!/usr/bin/env bash
set -e
cd "$HOME/scriptbot"
. .venv/bin/activate
exec python bot.py
