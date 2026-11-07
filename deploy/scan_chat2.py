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
print("fences:", full.count("```"))
print("lua fences:", len(re.findall(r"```(?:lua|luau)\b", full, re.IGNORECASE)))
print("FireServer:", full.count("FireServer"))
print("section:Toggle:", full.count("section:Toggle"))
print("Snowy Studios:", full.count("Snowy Studios"))
print("getgenv:", full.count("getgenv"))
for marker in ["```lua", "```luau", "Snowy -", "getgenv().__SnowHubAdapter", "First: one complete"]:
    i = full.find(marker)
    print(repr(marker), "at", i)
