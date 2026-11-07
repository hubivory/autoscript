import glob
import json
import os

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
print("chats:", len(files))
path = files[-1]
print("latest:", path)
data = json.load(open(path, encoding="utf-8"))
messages = data if isinstance(data, list) else data.get("messages", data)
print("type:", type(data).__name__, "count:", len(messages) if hasattr(messages, "__len__") else "?")
text = json.dumps(messages, ensure_ascii=False)
print("chars:", len(text))
open("/tmp/chat_dump.txt", "w", encoding="utf-8").write(text[:200000])
print("dumped head")
