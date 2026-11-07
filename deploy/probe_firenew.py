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
local home = root.Position
local function boardset()
  local s = {}
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
      s[tostring(d.ObjectText)] = d
    end
  end
  return s
end
local before = boardset()
local best, bestd, bestname = nil, 1e9, ""
local zones = Workspace:FindFirstChild("Build") and Workspace.Build:FindFirstChild("ZoneBuilds")
if zones then
for _, zone in ipairs(zones:GetChildren()) do
  local ef = zone:FindFirstChild("Eggs")
  local roots = {}
  if ef then roots = {ef} else roots = {zone} end
  for _, r2 in ipairs(roots) do
    for _, d in ipairs(r2:GetDescendants()) do
      if d:IsA("BasePart") and d.Parent and d.Name == "Egg" then
        local ok, pos = pcall(function() return d.Position end)
        if ok then
          local dist = (pos - root.Position).Magnitude
          if dist < bestd then best, bestd, bestname = d, dist, d.Parent.Name end
        end
      end
    end
  end
end
end
if not best then return "no egg" end
out[#out+1] = "killed=" .. bestname
local hum = char:FindFirstChildOfClass("Humanoid")
root.CFrame = CFrame.new(best.Position + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(0.5)
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
for i = 1, 60 do
  if not best.Parent then out[#out+1] = "dead@" .. i break end
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  task.wait(1.0)
end
if best.Parent then return "NOTKILLED" end
task.wait(2)
local after = boardset()
local newp = {}
for txt, d in pairs(after) do if not before[txt] then newp[#newp+1] = d end end
out[#out+1] = "newn=" .. #newp
local vim = game:GetService("VirtualInputManager")
for _, pr in ipairs(newp) do
  local ok, pos = pcall(function() return pr.Parent.Position end)
  if not ok then ok, pos = pcall(function() return pr.Parent:GetPivot().Position end) end
  if ok then
    root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 0))
    task.wait(1)
    vim:SendKeyEvent(true, Enum.KeyCode.E, false, game)
    task.wait(0.7)
    vim:SendKeyEvent(false, Enum.KeyCode.E, false, game)
    task.wait(2)
    out[#out+1] = "fired=" .. tostring(pr.ObjectText):gsub("<[^>]+>", ""):sub(1, 30)
  end
end
local held = {}
if char then for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
out[#out+1] = "xp=" .. tostring(p:GetAttribute("MasteryXp_Stealing"))
local plot = Workspace.Plots:FindFirstChild("Base_4")
out[#out+1] = "animals=" .. tostring(plot and plot:GetAttribute("AnimalsPlaced"))
root.CFrame = CFrame.new(home + Vector3.new(0, 3, 0))
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 115000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
