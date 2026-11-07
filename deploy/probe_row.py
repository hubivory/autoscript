import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FIND_ROW = """
local out = {}
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and txt == "Auto farm eggs" and d:IsA("TextLabel") then
    local row = d.Parent
    out[#out+1] = "label_parent=" .. row.ClassName .. ":" .. row.Name
    for _, sib in ipairs(row:GetChildren()) do
      out[#out+1] = " sib=" .. sib.ClassName .. ":" .. sib.Name
    end
    local card = row.Parent
    if card then
      out[#out+1] = "card=" .. card.ClassName .. ":" .. card.Name
    end
    break
  end
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": FIND_ROW})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
