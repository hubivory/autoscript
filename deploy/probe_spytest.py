import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FIRE = """
local rs = game:GetService("ReplicatedStorage")
local req = rs:FindFirstChild("EggHitRequest")
req:FireServer(Workspace)
task.wait(1)
return "fired"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()

        async def spy() -> str:
            try:
                return await mcp.call_tool("remote-spy", {"duration": 12})
            except Exception as exc:
                return f"SPY FAILED: {exc}"

        async def fire() -> str:
            await asyncio.sleep(3)
            try:
                return await mcp.call_tool("execute", {"code": FIRE})
            except Exception as exc:
                return f"FIRE FAILED: {exc}"

        spy_out, fire_out = await asyncio.gather(spy(), fire())
        print("fire:", (fire_out or "")[:150])
        await asyncio.sleep(2)
        console = await mcp.call_tool(
            "get-console-output", {"limit": 10, "filter": "MCP-SPY"}
        )
        print("=== spy console ===")
        print((console or "")[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
