import glob
import json
import re

pattern = "/home/ubuntu/.config/manicode/projects/fbcli_work/chats/*/chat-messages.json"
files = sorted(glob.glob(pattern))
for path in files[-1:]:
    data = json.load(open(path, encoding="utf-8"))
    messages = data if isinstance(data, list) else data.get("messages", [])
    for message in messages:
        role = message.get("role", "?")
        content = message.get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                p.get("text", "") for p in content if isinstance(p, dict)
            )
        print("=" * 30, role, len(content))
        if role == "assistant":
            blocks = re.findall(r"```(?:lua|luau)?\s*(.*?)```", content, re.DOTALL | re.IGNORECASE)
            print("code blocks:", len(blocks))
            if blocks:
                code = max(blocks, key=len)
                lines = code.splitlines()
                print("code lines:", len(lines))
                for i, line in enumerate(lines[:8], 1):
                    print(f"{i}: {line[:120]}")
