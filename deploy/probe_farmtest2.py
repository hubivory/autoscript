import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FIND_HIT = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and txt == "Auto farm eggs" and d:IsA("TextLabel") then
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

CASH = """
local p = game:GetService("Players").LocalPlayer
local v = p:GetAttribute("Cash")
return tostring(v)
"""

FARM_STATUS = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and txt and (string.find(txt, "Broke ") or string.find(txt, "Failed:") or txt == "Idle" or string.find(txt, "No eggs")) then
    return txt:sub(1, 120)
  end
end
return "no status"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        hit = await mcp.call_tool("get-data-by-code", {"code": FIND_HIT})
        print("hit path:", (hit or "")[:400])
        if "not found" in (hit or ""):
            return 1
        path = hit.strip().splitlines()[-1].strip()
        cash0 = await mcp.call_tool("get-data-by-code", {"code": CASH})
        print("cash before:", (cash0 or "")[:100])
        await mcp.call_tool("click-button", {"path": path, "action": "MouseButton1Click"})
        print("toggled ON, waiting 45s...")
        await asyncio.sleep(45)
        cash1 = await mcp.call_tool("get-data-by-code", {"code": CASH})
        print("cash after:", (cash1 or "")[:100])
        status = await mcp.call_tool("get-data-by-code", {"code": FARM_STATUS})
        print("farm status:", (status or "")[:200])
        await mcp.call_tool("click-button", {"path": path, "action": "MouseButton1Click"})
        print("toggled OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
