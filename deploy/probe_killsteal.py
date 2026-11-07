import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

KILL_STEAL = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local log = {}
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local confirms = {}
for _, name in ipairs({"EggHitConfirmed", "EggHitLanded", "EggHitRejected"}) do
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    r.OnClientEvent:Connect(function(a, b, c, d)
      if #confirms < 40 then
        local fmt = function(v)
          if typeof(v) == "Instance" then return v.ClassName .. ":" .. v.Name
          else return tostring(v) end
        end
        confirms[#confirms+1] = name .. "{" .. fmt(a) .. "|" .. fmt(b) .. "|" .. fmt(c) .. "|" .. fmt(d) .. "}"
      end
    end)
  end
end
local pp = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
if not pp then return "no char" end
local best, bestd = nil, 1e9
local builds = Workspace:FindFirstChild("Build")
local zones = builds and builds:FindFirstChild("ZoneBuilds")
if not zones then return "no zones" end
for _, zone in ipairs(zones:GetChildren()) do
  local ef = zone:FindFirstChild("Eggs")
  local roots = {}
  if ef then roots = {ef} else roots = {zone} end
  for _, root in ipairs(roots) do
    for _, d in ipairs(root:GetDescendants()) do
      if d:IsA("BasePart") and d.Parent then
        local isnest = string.find(d.Parent.Name, "Nest", 1, true) ~= nil
        if d.Name == "Egg" or (isnest and (d.Name == "p1" or d.Name == "p2")) then
          local ok, pos = pcall(function() return d.Position end)
          if ok then
            local dist = (pos - pp.Position).Magnitude
            if dist < bestd then best, bestd = d, dist end
          end
        end
      end
    end
  end
end
if not best then return "no egg" end
log[#log+1] = "target=" .. best:GetFullName() .. " dist=" .. math.floor(bestd)
local char = p.Character
local hum = char:FindFirstChildOfClass("Humanoid")
local root = char:FindFirstChild("HumanoidRootPart")
root.CFrame = CFrame.new(best.Position + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
task.wait(0.5)
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
local c0 = cash()
local killedAt, killCash = nil, nil
for i = 1, 30 do
  if not best.Parent then killedAt, killCash = i, cash() break end
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  task.wait(1.4)
end
if not killedAt then
  if not best.Parent then killedAt, killCash = 30, cash() end
end
log[#log+1] = string.format("killedAt=%s cash=%s->%s", tostring(killedAt), tostring(c0), tostring(cash()))
if killedAt then
  local kids = {}
  for _, c in ipairs(char:GetChildren()) do kids[#kids+1] = c.Name .. "." .. c.ClassName end
  log[#log+1] = "char=[" .. table.concat(kids, ",") .. "]"
  local attrs, keys = {}, {}
  for k, v in pairs(p:GetAttributes()) do keys[#keys+1] = k .. "=" .. tostring(v) end
  log[#log+1] = "pattrs=[" .. table.concat(keys, ",") .. "]"
  local drops = {}
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("BasePart") and (d.Name == "Drop" or d.Name == "Gem" or d.Name == "Loot" or string.find(d.Name, "Drop", 1, true)) then
      local ok, pos = pcall(function() return d.Position end)
      if ok and (pos - root.Position).Magnitude < 60 then drops[#drops+1] = d:GetFullName() end
      if #drops >= 8 then break end
    end
  end
  log[#log+1] = "drops=[" .. table.concat(drops, "|") .. "]"
  local suspects = {"EggGemDropRemote", "CatchFlingRemote", "DropCarriedRemote", "PlaceAnimalRemote", "AnimalBankedRemote", "BatHitRequest", "GuardMorphRemote", "FollowPetRemote"}
  for _, name in ipairs(suspects) do
    local r = rs:FindFirstChild(name)
    if r and r:IsA("RemoteEvent") then
      local before = cash()
      pcall(function() r:FireServer() end)
      task.wait(1)
      log[#log+1] = name .. " cash=" .. tostring(before) .. "->" .. tostring(cash())
    else
      log[#log+1] = name .. "=missing"
    end
  end
end
log[#log+1] = "confirms=[" .. table.concat(confirms, " ") .. "]"
return table.concat(log, " || ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool(
                "get-data-by-code", {"code": KILL_STEAL, "timeout": 120000}
            )
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
