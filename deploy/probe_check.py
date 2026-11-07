import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=60) as mcp:
        await mcp.list_tools()
        console = mcp.find_tool("get-console-output", "console")
        probe = mcp.find_tool("get-data-by-code", "data-by-code")
        if console:
            key = mcp.arg_key(console, "limit", "logsOrder", "filter", "summaryOnly")
            out = await mcp.call_tool(console, {"limit": 8})
            print("=== console (limit 8) ===")
            print(out[:3000])
        if probe:
            key = mcp.arg_key(probe, "code")
            args = {key: 'return game.PlaceId, game:GetService("Players").LocalPlayer.Name'}
            print("=== probe ===")
            print(await mcp.call_tool(probe, args))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
