import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FIND_TOGGLE = """
local found = nil
local hui = gethui and gethui()
local roots = {}
if hui then roots[#roots+1] = hui end
roots[#roots+1] = game:GetService("CoreGui")
for _, root in ipairs(roots) do
  for _, d in ipairs(root:GetDescendants()) do
    if (d:IsA("TextButton") or d:IsA("ImageButton")) then
      local ok, txt = pcall(function() return d.Text end)
      if ok and txt == "Auto farm eggs" then found = d:GetFullName() break end
      local ok2, kids = pcall(function()
        for _, c in ipairs(d:GetChildren()) do
          if c:IsA("TextLabel") and c.Text == "Auto farm eggs" then return true end
        end
        return false
      end)
      if ok2 and kids then found = d:GetFullName() break end
    end
  end
  if found then break end
end
return found or "not found"
"""

CASH = """
local p = game:GetService("Players").LocalPlayer
local v = p:GetAttribute("Cash")
return tostring(v)
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        path = await mcp.call_tool("get-data-by-code", {"code": FIND_TOGGLE})
        print("toggle:", (path or "")[:300])
        if "not found" in (path or ""):
            return 1
        toggle_path = path.strip().splitlines()[-1].strip()
        cash0 = await mcp.call_tool("get-data-by-code", {"code": CASH})
        print("cash before:", (cash0 or "")[:100])
        await mcp.call_tool("click-button", {"path": toggle_path, "action": "MouseButton1Click"})
        print("toggled ON, waiting 40s...")
        await asyncio.sleep(40)
        cash1 = await mcp.call_tool("get-data-by-code", {"code": CASH})
        print("cash after:", (cash1 or "")[:100])
        await mcp.call_tool("click-button", {"path": toggle_path, "action": "MouseButton1Click"})
        print("toggled OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
