#!/usr/bin/env bash
ls -td /tmp/fbcli_* 2>/dev/null | head -3
F=$(ls -t /tmp/fbcli_*/last_pane.txt 2>/dev/null | head -1)
echo "F=$F"
wc -c "$F"
echo "--- choose model ---"
grep -a -c 'choose model' "$F" || true
echo "--- opus ---"
grep -a -c -i 'opus' "$F" || true
echo "--- markers ---"
grep -a -c 'BEGIN' "$F" || true
grep -a -c 'PONG-MODEL' "$F" || true
echo "--- status ---"
grep -a -m3 'model to change' "$F" | cut -c1-160
