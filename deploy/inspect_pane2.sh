#!/usr/bin/env bash
F=/home/ubuntu/scriptbot/data/fbcli_work/last_pane.txt
wc -c "$F"
echo "--- choose model ---"
grep -a -c 'choose model' "$F" || true
echo "--- Opus/opus ---"
grep -a -c -i 'opus' "$F" || true
echo "--- markers ---"
grep -a -c 'BEGIN' "$F" || true
grep -a -c 'PONG-MODEL' "$F" || true
echo "--- status bar ---"
grep -a -m2 'model to change' "$F" | head -4
echo "--- tail 30 ---"
tail -c 3000 "$F"