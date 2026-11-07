#!/usr/bin/env bash
echo "--- load ---"
uptime
echo "--- tmux servers ---"
ls /tmp/tmux-* 2>/dev/null || echo "no tmux sockets?"
echo "--- node procs ---"
ps aux | grep -E 'tmux|freebuff' | grep -v grep | awk '{print $2, $11, $12, $13}' | head -20
