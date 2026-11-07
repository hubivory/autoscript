import glob
import json
import sys

sys.path.insert(0, "/home/ubuntu/scriptbot")
from llm import extract_lua

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
for path in files[-3:]:
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
    print("=" * 20, path.split("/")[-2])
    for i, text in enumerate(texts):
        if not text.strip():
            continue
        script = extract_lua(text)
        lines = script.splitlines()
        print(f"  text{i}: {len(text)} chars -> script {len(script)} chars / {len(lines)} lines")
        for j, line in enumerate(lines[:4], 1):
            print(f"    {j}: {line[:100]}")
