import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

LABELS = """
local out = {}
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" and #txt > 0 and #txt < 140 then
    local path = d:GetFullName()
    if string.find(path, "SnowyStudios", 1, true) then
      out[#out+1] = txt
    end
  end
end
return table.concat(out, " || ")
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


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        hit = await mcp.call_tool("get-data-by-code", {"code": FIND_HIT})
        path = hit.strip().splitlines()[-1].strip()
        print("toggle:", path[:200])
        if path == "not found":
            return 1
        await mcp.call_tool("click-button", {"path": path, "action": "MouseButton1Click"})
        print("ON")
        for round in (1, 2, 3):
            await asyncio.sleep(12)
            labels = await mcp.call_tool("get-data-by-code", {"code": LABELS})
            print(f"--- t+{round * 12}s ---")
            print((labels or "")[:2500])
        await mcp.call_tool("click-button", {"path": path, "action": "MouseButton1Click"})
        print("OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
