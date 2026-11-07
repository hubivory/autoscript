#!/usr/bin/env bash
pgrep -af 'run_first' | grep -v pgrep | head -2
echo "--- sessions ---"
for s in fbclia7c28990 fbcli73eede3b; do
  echo "== $s"
  tmux -L "$s" list-sessions 2>&1 | head -2
done
echo "--- workdir ---"
ls -la /home/ubuntu/scriptbot/data/fbcli_work/ 2>&1
