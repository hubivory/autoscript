import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q_LM = """
local out = {}
for _, d in ipairs(game:GetService("ReplicatedStorage"):GetDescendants()) do
  if d:IsA("RemoteEvent") or d:IsA("RemoteFunction") then
    local first = string.sub(d.Name, 1, 1)
    if (first >= "L" and first <= "M") then
      out[#out+1] = (d:IsA("RemoteEvent") and "E" or "F") .. ":" .. d.Name
    end
  end
end
table.sort(out)
return table.concat(out, ",")
"""

Q_KILL_SNAP = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
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
  for _, root2 in ipairs(roots) do
    for _, d in ipairs(root2:GetDescendants()) do
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
local function guardist()
  local gd = 1e9
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("Model") and string.find(d.Name, "uard", 1, true) then
      local ok, pos = pcall(function() return d:GetPivot().Position end)
      if ok then gd = math.min(gd, (pos - root.Position).Magnitude) end
    end
  end
  return gd
end
local g0 = guardist()
local hum = char:FindFirstChildOfClass("Humanoid")
root.CFrame = CFrame.new(best.Position + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(0.5)
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
local c0 = cash()
local killedAt = nil
for i = 1, 30 do
  if not best.Parent then killedAt = i break end
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  task.wait(1.4)
end
task.wait(1)
local g1 = guardist()
local out = {}
out[#out+1] = "killedAt=" .. tostring(killedAt)
out[#out+1] = "cash=" .. tostring(c0) .. "->" .. tostring(cash())
out[#out+1] = "guard=" .. math.floor(g0) .. "->" .. math.floor(g1)
for k, v in pairs(p:GetAttributes()) do
  local ks = tostring(k)
  if string.find(ks, "arry", 1, true) or string.find(ks, "teal", 1, true) or string.find(ks, "gg", 1, true) or string.find(ks, "ank", 1, true) or string.find(ks, "arry", 1, true) then
    out[#out+1] = ks .. "=" .. tostring(v)
  end
end
local tools = {}
for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then tools[#tools+1] = t.Name end end
for _, t in ipairs(p.Backpack:GetChildren()) do if t:IsA("Tool") then tools[#tools+1] = "pack:" .. t.Name end end
out[#out+1] = "tools=[" .. table.concat(tools, ",") .. "]"
return table.concat(out, " ")
"""


async def gdc(mcp, code, timeout=90):
    out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    return (out or "")[:2200]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        for label, code in (("lm", Q_LM), ("killsnap", Q_KILL_SNAP)):
            try:
                print(f"=== {label} ===", flush=True)
                print(await gdc(mcp, code), flush=True)
            except Exception as exc:
                print(f"{label} FAILED: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
