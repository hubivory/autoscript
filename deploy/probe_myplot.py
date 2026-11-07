import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {"me=" .. tostring(p.UserId)}
for _, plot in ipairs(Workspace.Plots:GetChildren()) do
  out[#out+1] = plot.Name .. ":" .. tostring(plot:GetAttribute("OwnerUserId")) .. "/" .. tostring(plot:GetAttribute("AnimalsPlaced"))
end
return table.concat(out, " ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=60) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:800])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
