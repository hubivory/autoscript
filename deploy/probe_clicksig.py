import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

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

FARM_STATUS = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" then
    if txt == "Idle" or string.find(txt, "Broke ", 1, true) or string.find(txt, "Failed:", 1, true) or string.find(txt, "No eggs", 1, true) or string.find(txt, "Travel:", 1, true) or string.find(txt, "Scanning", 1, true) then
      return txt:sub(1, 100)
    end
  end
end
return "none"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        hit = await mcp.call_tool("get-data-by-code", {"code": FIND_HIT})
        path = hit.strip().splitlines()[-1].strip()
        print("toggle:", path[:150])
        for action in ("Activated", "MouseButton1Down", "MouseButton1Click"):
            await mcp.call_tool("click-button", {"path": path, "action": action})
            await asyncio.sleep(4)
            status = await mcp.call_tool("get-data-by-code", {"code": FARM_STATUS})
            line = (status or "").strip().splitlines()[-1][:100]
            print(f"{action}: status={line}")
            if "Idle" not in line:
                print("TOGGLE RESPONDED")
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
