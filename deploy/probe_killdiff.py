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
local function board()
  local names = {}
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
      local txt = tostring(d.ObjectText):gsub("<[^>]+>", ""):gsub("%s+", " ")
      names[#names+1] = txt:sub(1, 32)
    end
  end
  return names
end
local before = board()
out[#out+1] = "before=" .. #before
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
if best then
  out[#out+1] = "killing=" .. bestname
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
end
task.wait(2)
local after = board()
out[#out+1] = "after=" .. #after
local bset = {}
for _, n in ipairs(before) do bset[n] = true end
local newones = {}
for _, n in ipairs(after) do if not bset[n] then newones[#newones+1] = n end end
out[#out+1] = "new=[" .. table.concat(newones, "|") .. "]"
return table.concat(out, " || ")
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
