import glob
import json
import re

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-1]
data = json.load(open(path, encoding="utf-8"))
print("messages:", len(data))
for i, message in enumerate(data):
    if not isinstance(message, dict):
        continue
    variant = message.get("variant")
    content = message.get("content") or ""
    blocks = message.get("blocks") or []
    texts = [content]
    for block in blocks:
        if isinstance(block, dict):
            for key in ("text", "output", "result"):
                value = block.get(key)
                if isinstance(value, str):
                    texts.append(value)
    joined = "\n".join(texts)
    has_lua = "```lua" in joined or "```luau" in joined
    has_snowy = "Snowy" in joined or "getgenv" in joined
    print(f"{i}: variant={variant} chars={len(joined)} lua={has_lua} snowy={has_snowy}")
