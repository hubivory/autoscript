import glob
import json


def walk(value: object, path: str, out: list) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            walk(item, f"{path}.{key}", out)
    elif isinstance(value, list):
        out.append((path, f"list[{len(value)}]"))
        for i, item in enumerate(value[:12]):
            walk(item, f"{path}[{i}]", out)
    elif isinstance(value, str):
        if len(value) > 2000:
            out.append((path, f"str[{len(value)}] head={value[:90]!r}"))
    else:
        out.append((path, f"{type(value).__name__}={value}"))


pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
path = files[-2]
print("chat:", path.split("/")[-2])
data = json.load(open(path, encoding="utf-8"))
out: list = []
walk(data, "root", out)
for item in out:
    print(item)
