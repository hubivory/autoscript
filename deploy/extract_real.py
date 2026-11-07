import glob
import json
import re
import sys

sys.path.insert(0, "/home/ubuntu/scriptbot")
from llm import extract_lua

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-2]
data = json.load(open(path, encoding="utf-8"))
for message in data:
    if not isinstance(message, dict):
        continue
    for block in message.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        content = block.get("content") or ""
        if len(content) > 20000 and "```lua" in content:
            script = extract_lua(content)
            lines = script.splitlines()
            print("script chars:", len(script), "lines:", len(lines))
            open("/tmp/attempt2_script.lua", "w", encoding="utf-8").write(script)
            for i, line in enumerate(lines[:12], 1):
                print(f"{i}: {line[:120]}")
