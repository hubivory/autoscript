import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local rs = game:GetService("ReplicatedStorage")
local out = {}
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if not root then return "no char" end
local function gstate()
  local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
  if not ag then return "noag" end
  return "chase=" .. tostring(ag:GetAttribute("ChaseState")) .. " caught=" .. tostring(ag:GetAttribute("CaughtUserId")) .. " pulse=" .. tostring(ag:GetAttribute("CatchPulse"))
end
local z10 = Workspace.Build.ZoneBuilds.Zone10
local ef = z10 and z10:FindFirstChild("Eggs")
local best = nil
if ef then
  for _, m in ipairs(ef:GetChildren()) do
    if string.find(m.Name, "Plasma", 1, true) then
      local egg = m:FindFirstChild("Egg")
      if egg and egg:IsA("BasePart") then best = egg break end
    end
  end
end
if not best then return "no plasma egg" end
out[#out+1] = "target=" .. best.Parent.Name
out[#out+1] = "g0 " .. gstate()
local hum = char:FindFirstChildOfClass("Humanoid")
root.CFrame = CFrame.new(best.Position + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(0.5)
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
local c0 = p:GetAttribute("Cash")
local killedAt = nil
for i = 1, 30 do
  if not best.Parent then killedAt = i break end
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  if i % 5 == 0 then out[#out+1] = "i" .. i .. " " .. gstate() end
  task.wait(1.2)
end
out[#out+1] = "killedAt=" .. tostring(killedAt) .. " cash=" .. tostring(c0) .. "->" .. tostring(p:GetAttribute("Cash"))
out[#out+1] = "g1 " .. gstate()
local tools = {}
for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then tools[#tools+1] = t.Name end end
out[#out+1] = "held=[" .. table.concat(tools, ",") .. "]"
if killedAt then
  task.wait(3)
  out[#out+1] = "g2 " .. gstate()
  local myplot = Workspace.Plots:FindFirstChild("Base_4")
  if myplot then
    local ok, pos = pcall(function() return myplot:GetPivot().Position end)
    if ok then
      root.CFrame = CFrame.new(pos + Vector3.new(0, 5, 0))
      task.wait(2)
      out[#out+1] = "escaped " .. gstate()
    end
  end
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 120000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
