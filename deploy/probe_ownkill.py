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
local best, bestd, bestname = nil, 1e9, ""
local zones = Workspace:FindFirstChild("Build") and Workspace.Build:FindFirstChild("ZoneBuilds")
if not zones then return "no zones" end
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
local xp0 = p:GetAttribute("MasteryXp_Stealing")
for i = 1, 30 do
  if not best.Parent then break end
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  task.wait(1.4)
end
if best.Parent then return "NOTKILLED" end
local prompt, pd = nil, 1e9
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
    local ok, pos = pcall(function() return d.Parent.Position end)
    if not ok then ok, pos = pcall(function() return d.Parent:GetPivot().Position end) end
    if ok then
      local dist = (pos - root.Position).Magnitude
      if dist < pd then prompt, pd = d, dist end
    end
  end
end
if not prompt then return table.concat(out, " ") .. " NOPROMPT" end
out[#out+1] = "prompt=" .. tostring(prompt.ObjectText):sub(1, 60) .. " @" .. math.floor(pd)
local ok, pos = pcall(function() return prompt.Parent.Position end)
if not ok then ok, pos = pcall(function() return prompt.Parent:GetPivot().Position end) end
if ok then root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 0)) task.wait(1) end
local fpp = fireproximityprompt or fire_proximity_prompt
if type(fpp) == "function" then pcall(function() fpp(prompt) end) end
task.wait(3)
out[#out+1] = "xp=" .. tostring(xp0) .. "->" .. tostring(p:GetAttribute("MasteryXp_Stealing"))
local held = {}
if char then for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) end
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
