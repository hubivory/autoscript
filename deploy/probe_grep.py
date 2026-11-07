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
        await mcp.list_tools()
        for pattern in ("StealPrompt", "PromptAnchor"):
            try:
                out = await mcp.call_tool("script-grep", {"query": pattern, "limit": 20})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {pattern} ===", flush=True)
            print((out or "")[:2500], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
