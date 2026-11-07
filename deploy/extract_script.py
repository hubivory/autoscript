import glob
import json
import re

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-1]
data = json.load(open(path, encoding="utf-8"))
texts = []
for message in data:
    if not isinstance(message, dict) or message.get("variant") != "ai":
        continue
    content = message.get("content") or ""
    texts.append(content)
    for block in message.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        for key in ("text", "output", "result"):
            value = block.get(key)
            if isinstance(value, str) and len(value) > 200:
                texts.append(value[:200000])
full = "\n".join(texts)
print("ai text chars:", len(full))
blocks = re.findall(r"```(?:lua|luau)?\s*(.*?)```", full, re.DOTALL | re.IGNORECASE)
print("code blocks:", len(blocks))
if blocks:
    code = max(blocks, key=len)
    lines = code.splitlines()
    print("code lines:", len(lines))
    open("/tmp/attempt3.lua", "w", encoding="utf-8").write(code)
    for i, line in enumerate(lines[:10], 1):
        print(f"{i}: {line[:130]}")
