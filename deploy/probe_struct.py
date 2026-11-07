import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

STRUCT_PROBE = """
local out = {}
local plots = Workspace:FindFirstChild("Plots")
if not plots then return "no Plots" end
local pkids = plots:GetChildren()
out[#out+1] = "plots=" .. #pkids
local first = pkids[1]
if first then
  out[#out+1] = "firstplot=" .. first.Name .. "." .. first.ClassName
  local kids = first:GetChildren()
  out[#out+1] = "plotkids=" .. #kids
  for i = 1, math.min(15, #kids) do
    local c = kids[i]
    out[#out+1] = " kid=" .. c.Name .. "." .. c.ClassName
  end
end
local found = 0
for _, d in ipairs(plots:GetDescendants()) do
  if found >= 25 then break end
  local n = string.lower(d.Name)
  if string.find(n, "egg", 1, true) then
    found = found + 1
    local parent = d.Parent
    out[#out+1] = "eggish=" .. d.Name .. "." .. d.ClassName .. " parent=" .. (parent and parent.Name .. "." .. parent.ClassName or "?")
  end
end
out[#out+1] = "eggish_total=" .. found
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": STRUCT_PROBE})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
