import glob
import json

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-1]
data = json.load(open(path, encoding="utf-8"))
if isinstance(data, list):
    for i, message in enumerate(data[:6]):
        print(i, type(message).__name__, str(message)[:300])
else:
    print(type(data).__name__, list(data.keys())[:10])
