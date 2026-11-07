import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        tools = await mcp.list_tools()
        names = sorted([t if isinstance(t, str) else t.get("name", "?") for t in tools] if isinstance(tools, list) else [])
        print("TOOLS:", " ".join(names))
        for target in ("script-grep", "get-signal-connections", "get-script-content"):
            if target in names:
                print(f"HAS {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
