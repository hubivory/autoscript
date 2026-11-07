import glob
import json
import re

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-1]
data = json.load(open(path, encoding="utf-8"))
joined = []
for message in data:
    if not isinstance(message, dict) or message.get("variant") != "ai":
        continue
    joined.append(message.get("content") or "")
    for block in message.get("blocks") or []:
        if isinstance(block, dict):
            for key in ("text", "output", "result"):
                value = block.get(key)
                if isinstance(value, str):
                    joined.append(value)
full = "\n".join(joined)
parts = re.split(r"```(?:lua|luau)?\s*", full, flags=re.DOTALL | re.IGNORECASE)
print("parts:", len(parts))
for i, part in enumerate(parts[1:], 1):
    end = part.find("```")
    code = part[:end] if end != -1 else part
    lines = code.splitlines()
    print(f"--- block {i}: {len(lines)} lines, closed={end != -1}")
    for j, line in enumerate(lines[:6], 1):
        print(f"  {j}: {line[:110]}")
