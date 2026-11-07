import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FIND_NEST = """
local p = game:GetService("Players").LocalPlayer
local pp = p.Character:FindFirstChild("HumanoidRootPart").Position
local best, bestd, bestpos = nil, 1e9, nil
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") and string.find(d.Name, "Nest", 1, true) then
    local ok, pv = pcall(function() return d:GetPivot().Position end)
    if ok then
      local dist = (pv - pp).Magnitude
      if dist < bestd then best, bestd, bestpos = d:GetFullName(), dist, pv end
    end
  end
end
if bestpos then
  return string.format("%s|%.0f|%.0f,%.0f,%.0f", best, bestd, bestpos.X, bestpos.Y, bestpos.Z)
end
return "none"
"""

WALK_SWING = """
local p = game:GetService("Players").LocalPlayer
local char = p.Character
local hum = char:FindFirstChildOfClass("Humanoid")
local root = char:FindFirstChild("HumanoidRootPart")
local tx, ty, tz = %TARGET%
hum:MoveTo(Vector3.new(tx, ty, tz))
local t0 = os.clock()
while os.clock() - t0 < 12 do
  local d = (root.Position - Vector3.new(tx, ty, tz)).Magnitude
  if d < 18 then break end
  task.wait(0.3)
end
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(1)
for i = 1, 4 do
  local tool = char:FindFirstChildOfClass("Tool")
  if tool then tool:Activate() end
  task.wait(1.2)
end
local d = (root.Position - Vector3.new(tx, ty, tz)).Magnitude
return string.format("dist=%.0f", d)
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        nest = await mcp.call_tool("get-data-by-code", {"code": FIND_NEST})
        print("nest:", (nest or "")[:300])
        match = re.search(r"\|(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)", nest or "")
        if not match:
            print("no nest target")
            return 1
        tx, ty, tz = match.groups()
        walk = WALK_SWING.replace("%TARGET%", f"{tx}, {ty}, {tz}")

        async def spy() -> str:
            try:
                return await mcp.call_tool("remote-spy", {"duration": 25})
            except Exception as exc:
                return f"SPY FAILED: {exc}"

        async def swing() -> str:
            await asyncio.sleep(3)
            try:
                return await mcp.call_tool("execute", {"code": walk})
            except Exception as exc:
                return f"SWING FAILED: {exc}"

        spy_out, swing_out = await asyncio.gather(spy(), swing())
        print("swing:", (swing_out or "")[:200])
        console = await mcp.call_tool(
            "get-console-output", {"limit": 30, "filter": "MCP-SPY"}
        )
        print("=== spy console ===")
        print((console or "")[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
