import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

EGG_MAP = """
local out = {}
local eggsFolder = Workspace:FindFirstChild("Eggs")
if not eggsFolder then return "no Eggs folder" end
local kids = eggsFolder:GetChildren()
out[#out+1] = "eggskids=" .. #kids
for i = 1, math.min(10, #kids) do
  local z = kids[i]
  out[#out+1] = " zone=" .. z.Name .. "." .. z.ClassName .. " kids=" .. #z:GetChildren()
  local sub = z:GetChildren()
  for j = 1, math.min(6, #sub) do
    local e = sub[j]
    local detail = e.Name .. "." .. e.ClassName
    if e:IsA("Model") or e:IsA("Folder") then
      detail = detail .. "(" .. #e:GetChildren() .. ")"
    end
    if e:IsA("BasePart") then
      local p = e.Position
      detail = detail .. string.format("@%.0f,%.0f,%.0f", p.X, p.Y, p.Z)
    end
    out[#out+1] = "  - " .. detail
  end
end
local p = game:GetService("Players").LocalPlayer
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if root then
  local v = root.Position
  out[#out+1] = string.format("player@%.0f,%.0f,%.0f", v.X, v.Y, v.Z)
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": EGG_MAP})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
