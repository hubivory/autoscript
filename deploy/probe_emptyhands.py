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
local hum = char and char:FindFirstChildOfClass("Humanoid")
if not root or not hum then return "no char" end
hum:UnequipTools()
task.wait(0.5)
local pa = Workspace.Plots.Base_3:FindFirstChild("PlacedAnimals")
local animal = pa and (pa:FindFirstChild("Tiger") or pa:GetChildren()[1])
if not animal then return "no animal" end
out[#out+1] = "animal=" .. animal.Name
local ok, pos = pcall(function() return animal:GetPivot().Position end)
if ok then root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 1)) end
task.wait(4)
local held = {}
for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
local st = {}
for k, v in pairs(p:GetAttributes()) do
  local ks = tostring(k)
  if string.find(ks, "teal", 1, true) or string.find(ks, "arry", 1, true) then st[#st+1] = ks .. "=" .. tostring(v) end
end
out[#out+1] = "stealattrs=[" .. table.concat(st, ",") .. "]"
local gd = 1e9
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then
  out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) .. " caught=" .. tostring(ag:GetAttribute("CaughtUserId"))
  local ok2, pos2 = pcall(function() return ag:GetPivot().Position end)
  if ok2 then gd = (pos2 - root.Position).Magnitude end
end
out[#out+1] = "guard=" .. math.floor(gd)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then hum:EquipTool(t) break end
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 60000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
