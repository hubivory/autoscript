#!/usr/bin/env bash
F=$(find /tmp -maxdepth 2 -name last_pane.txt 2>/dev/null | head -1)
echo "file=$F"
wc -c "$F"
echo "--- pong count ---"
grep -a -c 'PONG-CLIPROBE' "$F" || true
echo "--- begin count ---"
grep -a -c 'BEGIN' "$F" || true
echo "--- context ---"
grep -a -m3 -B4 -A8 'PONG-CLIPROBE' "$F" | head -50
