#!/usr/bin/env bash
echo "--- top cpu ---"
ps -eo pid,ppid,%cpu,%mem,comm,args --sort=-%cpu | head -12
echo "--- clean dead tmux sockets ---"
for s in /tmp/tmux-*; do
  sock=$(basename "$s")
  tmux -L "$sock" kill-server >/dev/null 2>&1 || rm -rf "$s"
done
ls /tmp/tmux-* 2>/dev/null || echo "sockets cleaned"
