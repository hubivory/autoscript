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
        me = await mcp.call_tool(
            "get-data-by-code", {"code": "return game:GetService('Players').LocalPlayer.Name"}
        )
        print("localplayer:", (me or "")[:200])
        for path in [
            "Players.SunFrReal.PlayerScripts.RbxCharacterSounds",
            "Players.SunFrReal.PlayerScripts.Client",
        ]:
            try:
                out = await mcp.call_tool("get-script-content", {"scriptPath": path})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {path} ===")
            print((out or "")[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
