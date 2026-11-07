import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_env

load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
token = os.getenv("DISCORD_TOKEN", "")
if not token or "." not in token:
    print("DISCORD_TOKEN missing or malformed")
    raise SystemExit(1)
user_id = token.split(".")[0]
pad = "=" * (-len(user_id) % 4)
client_id = base64.urlsafe_b64decode(user_id + pad).decode()
permissions = 1024 + 16 + 2048 + 16384 + 32768 + 65536
print(
    "https://discord.com/oauth2/authorize"
    f"?client_id={client_id}&permissions={permissions}&scope=bot+applications.commands"
)
