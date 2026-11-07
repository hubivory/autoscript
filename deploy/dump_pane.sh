#!/usr/bin/env bash
F=$(ls -t /tmp/fbcli_*/last_pane.txt 2>/dev/null | head -1)
python3 - "$F" <<'EOF'
import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
src = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", src)
src = re.sub(r"\x1b\][^\x07]*\x07", "", src)
lines = [l.rstrip() for l in src.splitlines() if l.strip()]
print("nonempty lines:", len(lines))
for line in lines:
    print(repr(line[:150]))
EOF