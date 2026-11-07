import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FIND_ANY = """
local found = {}
local hui = gethui and gethui()
local roots = {}
if hui then roots[#roots+1] = hui end
roots[#roots+1] = game:GetService("CoreGui")
for _, root in ipairs(roots) do
  for _, d in ipairs(root:GetDescendants()) do
    local ok, txt = pcall(function() return d.Text end)
    if ok and txt == "Auto farm eggs" then
      found[#found+1] = d.ClassName .. ":" .. d:GetFullName()
      if #found >= 5 then break end
    end
  end
  if #found >= 5 then break end
end
local guis = {}
if hui then
  for _, g in ipairs(hui:GetChildren()) do
    if g:IsA("ScreenGui") then guis[#guis+1] = g.Name end
  end
end
return "labels=" .. table.concat(found, " | ") .. " || guis=" .. table.concat(guis, ",")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": FIND_ANY})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
