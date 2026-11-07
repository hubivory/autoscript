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
local best, bestd = nil, 1e9
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
          if dist < bestd then best, bestd = d, dist end
        end
      end
    end
  end
end
if not best then return "no egg" end
local killpos = best.Position
local hum = char:FindFirstChildOfClass("Humanoid")
root.CFrame = CFrame.new(killpos + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(0.5)
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
local killedAt = nil
for i = 1, 30 do
  if not best.Parent then killedAt = i break end
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  task.wait(1.4)
end
out[#out+1] = "killedAt=" .. tostring(killedAt)
if killedAt then
  local near = {}
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("Model") and d.Name ~= "Chicken" then
      local ok, pos = pcall(function() return d:GetPivot().Position end)
      if ok and (pos - killpos).Magnitude < 40 then
        near[#near+1] = d.Name .. "@" .. math.floor((pos - killpos).Magnitude)
        if #near >= 12 then break end
      end
    end
  end
  out[#out+1] = "near=[" .. table.concat(near, "|") .. "]"
  local tools = {}
  for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then tools[#tools+1] = t.Name end end
  out[#out+1] = "held=[" .. table.concat(tools, ",") .. "]"
  local c = {}
  for k, v in pairs(char:GetAttributes()) do c[#c+1] = k .. "=" .. tostring(v) end
  out[#out+1] = "cattrs=[" .. table.concat(c, ",") .. "]"
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 120000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
