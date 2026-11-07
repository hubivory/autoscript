import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

CASH = """
local p = game:GetService("Players").LocalPlayer
return "cash=" .. tostring(p:GetAttribute("Cash"))
"""

FIND_HIT = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" and txt == "Auto farm eggs" and d:IsA("TextLabel") then
    local row = d.Parent
    for _, sib in ipairs(row:GetChildren()) do
      if sib:IsA("TextButton") and sib.Name == "Hit" then
        return sib:GetFullName()
      end
    end
  end
end
return "not found"
"""


async def gdc(mcp: MCPClient, code: str) -> str:
    out = await mcp.call_tool("get-data-by-code", {"code": code})
    match = re.search(r'"([^"]*)"', out or "")
    return match.group(1) if match else (out or "")[:120]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        path = await gdc(mcp, FIND_HIT)
        print("toggle:", path[:150])
        if path == "not found":
            return 1
        base = await gdc(mcp, CASH)
        print("t0:", base)
        await asyncio.sleep(60)
        off = await gdc(mcp, CASH)
        print("t60 OFF:", off)
        await mcp.call_tool("click-button", {"path": path, "action": "MouseButton1Click"})
        print("ON")
        await asyncio.sleep(60)
        on = await gdc(mcp, CASH)
        print("t120 ON:", on)
        await mcp.call_tool("click-button", {"path": path, "action": "MouseButton1Click"})
        print("OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
