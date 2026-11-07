import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

FARMCHAIN = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local log = {}
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local conf = 0
local landed = rs:FindFirstChild("EggHitLanded")
if landed and landed:IsA("RemoteEvent") then
  landed.OnClientEvent:Connect(function() conf = conf + 1 end)
end
local eggs = {}
local builds = Workspace:FindFirstChild("Build")
local zones = builds and builds:FindFirstChild("ZoneBuilds")
if zones then
  for _, zone in ipairs(zones:GetChildren()) do
    local ef = zone:FindFirstChild("Eggs")
    local roots = ef and {ef} or {zone}
    for _, root in ipairs(roots) do
      for _, d in ipairs(root:GetDescendants()) do
        if d:IsA("BasePart") and d.Parent and string.find(d.Parent.Name, "Nest", 1, true) then
          eggs[#eggs+1] = d
        end
      end
    end
  end
end
log[#log+1] = "eggs=" .. #eggs
if #eggs == 0 then return table.concat(log, " ") end
local char = p.Character
local root = char:FindFirstChild("HumanoidRootPart")
local hum = char:FindFirstChildOfClass("Humanoid")
local target = eggs[1]
root.CFrame = CFrame.new(target.Position + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(0.8)
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
local c0 = cash()
for i = 1, 5 do
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(target) end)
  task.wait(1.5)
end
local c1 = cash()
log[#log+1] = string.format("cash=%s->%s landed=%d", tostring(c0), tostring(c1), conf))
return table.concat(log, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool(
                "get-data-by-code", {"code": FARMCHAIN, "timeout": 60000}
            )
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
