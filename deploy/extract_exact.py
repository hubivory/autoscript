import glob
import json
import re
import sys

sys.path.insert(0, "/home/ubuntu/scriptbot")
from llm import extract_lua

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-1]
data = json.load(open(path, encoding="utf-8"))
texts = []
for message in data:
    if not isinstance(message, dict) or message.get("variant") != "ai":
        continue
    texts.append(message.get("content") or "")
    for block in message.get("blocks") or []:
        if isinstance(block, dict):
            for key in ("text", "output", "result"):
                value = block.get(key)
                if isinstance(value, str):
                    texts.append(value)
for i, text in enumerate(texts):
    if not text.strip():
        continue
    print(f"--- ai text {i}: {len(text)} chars")
    script = extract_lua(text)
    print(f"    extracted: {len(script)} chars, {len(script.splitlines())} lines")
    for j, line in enumerate(script.splitlines()[:6], 1):
        print(f"    {j}: {line[:110]}")
