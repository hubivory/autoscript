import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

NEST_POS = """
local out = {}
local p = game:GetService("Players").LocalPlayer
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
local pp = root and root.Position
if pp then
  out[#out+1] = string.format("player@%.0f,%.0f,%.0f", pp.X, pp.Y, pp.Z)
end
local count = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if count >= 12 then break end
  if d:IsA("Model") and string.find(d.Name, "Nest", 1, true) then
    local pivot = nil
    pcall(function() pivot = d:GetPivot().Position end)
    if pivot and pp then
      local dist = (pivot - pp).Magnitude
      count = count + 1
      out[#out+1] = string.format("%s@%.0f,%.0f,%.0f dist=%.0f", d:GetFullName(), pivot.X, pivot.Y, pivot.Z, dist)
    end
  end
end
out[#out+1] = "nestcount=" .. count
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": NEST_POS})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:3500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
