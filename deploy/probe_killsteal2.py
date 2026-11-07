import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

PART1 = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
getgenv().__confirms = {}
for _, name in ipairs({"EggHitConfirmed", "EggHitLanded", "EggHitRejected"}) do
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    r.OnClientEvent:Connect(function(a, b, c, d)
      local t = getgenv().__confirms
      if #t < 60 then
        local fmt = function(v)
          if typeof(v) == "Instance" then return v.ClassName .. ":" .. v.Name
          else return tostring(v) end
        end
        t[#t+1] = name .. "{" .. fmt(a) .. "|" .. fmt(b) .. "|" .. fmt(c) .. "|" .. fmt(d) .. "}"
      end
    end)
  end
end
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local pp = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
if not pp then return "no char" end
local best, bestd = nil, 1e9
local zones = Workspace:FindFirstChild("Build") and Workspace.Build:FindFirstChild("ZoneBuilds")
if not zones then return "no zones" end
for _, zone in ipairs(zones:GetChildren()) do
  local ef = zone:FindFirstChild("Eggs")
  local roots = {}
  if ef then roots = {ef} else roots = {zone} end
  for _, root in ipairs(roots) do
    for _, d in ipairs(root:GetDescendants()) do
      if d:IsA("BasePart") and d.Parent and d.Name == "Egg" then
        local ok, pos = pcall(function() return d.Position end)
        if ok then
          local dist = (pos - pp.Position).Magnitude
          if dist < bestd then best, bestd = d, dist end
        end
      end
    end
  end
end
if not best then return "no egg" end
getgenv().__farmTarget = best
local char = p.Character
local hum = char:FindFirstChildOfClass("Humanoid")
char:FindFirstChild("HumanoidRootPart").CFrame = CFrame.new(best.Position + Vector3.new(0, 4, 6))
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
return string.format("target=%s killedAt=%s cash=%s->%s nconf=%d", best:GetFullName(), tostring(killedAt), tostring(c0), tostring(cash()), #getgenv().__confirms)
"""

PART2 = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local out = {}
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
local kids = {}
if char then for _, c in ipairs(char:GetChildren()) do kids[#kids+1] = c.Name end end
out[#out+1] = "charn=" .. #kids
local tcount = 0
for _, c in ipairs(char:GetChildren()) do if c:IsA("Tool") then tcount = tcount + 1 end end
out[#out+1] = "heldtools=" .. tcount
local attrs = {}
for k, v in pairs(p:GetAttributes()) do attrs[#attrs+1] = k .. "=" .. tostring(v) end
out[#out+1] = "pattrs=[" .. table.concat(attrs, ",") .. "]"
local cattrs = {}
if char then for k, v in pairs(char:GetAttributes()) do cattrs[#cattrs+1] = k .. "=" .. tostring(v) end end
out[#out+1] = "cattrs=[" .. table.concat(cattrs, ",") .. "]"
local drops = {}
if root then
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("BasePart") or d:IsA("Model") then
      local n = d.Name
      if n == "Drop" or n == "Gem" or n == "Loot" or string.find(n, "Drop", 1, true) or string.find(n, "Loot", 1, true) or string.find(n, "Gem", 1, true) then
        local ok, pos = pcall(function()
          if d:IsA("Model") then return d:GetPivot().Position else return d.Position end
        end)
        if ok and (pos - root.Position).Magnitude < 80 then drops[#drops+1] = n .. "@" .. math.floor((pos - root.Position).Magnitude) end
        if #drops >= 10 then break end
      end
    end
  end
end
out[#out+1] = "drops=[" .. table.concat(drops, "|") .. "]"
for _, name in ipairs({"EggGemDropRemote", "CatchFlingRemote", "DropCarriedRemote", "PlaceAnimalRemote", "AnimalBankedRemote", "BatHitRequest", "GuardMorphRemote", "FollowPetRemote"}) do
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    local before = cash()
    pcall(function() r:FireServer() end)
    task.wait(1)
    out[#out+1] = name .. ":" .. tostring(before) .. "->" .. tostring(cash())
  else
    out[#out+1] = name .. "=missing"
  end
end
local conf = getgenv().__confirms or {}
local tail = {}
for i = math.max(1, #conf - 11), #conf do tail[#tail+1] = conf[i] end
out[#out+1] = "confirms=[" .. table.concat(tail, " ") .. "]"
return table.concat(out, " || ")
"""


async def gdc(mcp, code, timeout):
    out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    return out or ""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        print("=== PART1 ===", flush=True)
        try:
            print(await gdc(mcp, PART1, 120), flush=True)
        except Exception as exc:
            print(f"PART1 FAILED: {exc}", flush=True)
        print("=== PART2 ===", flush=True)
        try:
            print(await gdc(mcp, PART2, 120), flush=True)
        except Exception as exc:
            print(f"PART2 FAILED: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
