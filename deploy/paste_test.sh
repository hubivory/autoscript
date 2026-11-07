#!/usr/bin/env bash
printf '%s' '{"content":"print(1)","language":"lua","title":"mcp-test"}' > /tmp/paste_test.json
curl -s -m 30 -X POST https://paste-void.lovable.app/api/paste -H 'Content-Type: application/json' --data @/tmp/paste_test.json
echo
