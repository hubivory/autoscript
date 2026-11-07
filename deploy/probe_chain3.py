import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

SCAN = """
local eggs = {}
local builds = Workspace:FindFirstChild("Build")
local zones = builds and builds:FindFirstChild("ZoneBuilds")
if zones then
  for _, zone in ipairs(zones:GetChildren()) do
    local ef = zone:FindFirstChild("Eggs")
    local roots = {}
    if ef then roots = {ef} else roots = {zone} end
    for _, root in ipairs(roots) do
      for _, d in ipairs(root:GetDescendants()) do
        if d:IsA("BasePart") and d.Parent and string.find(d.Parent.Name, "Nest", 1, true) then
          local ok, path = pcall(function() return d:GetFullName() end)
          if ok then eggs[#eggs+1] = path end
        end
      end
    end
  end
end
getgenv().__farmEggList = eggs
return "eggs=" .. #eggs
"""

MOVE_EQUIP = """
local p = game:GetService("Players").LocalPlayer
local list = getgenv().__farmEggList
if not list or #list == 0 then return "no list" end
local svc = game:GetService("ReplicatedStorage")
local part = nil
for _, path in ipairs(list) do
  local ok, inst = pcall(function()
    local node = game
    for seg in string.gmatch(path, "[^%.]+") do node = node[seg] end
    return node
  end)
  if ok and inst and inst.Parent then part = inst break end
end
if not part then return "no live part" end
local char = p.Character
local root = char:FindFirstChild("HumanoidRootPart")
root.CFrame = CFrame.new(part.Position + Vector3.new(0, 4, 6))
task.wait(1)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then char:FindFirstChildOfClass("Humanoid"):EquipTool(t) break end
end
task.wait(0.5)
local tool = char:FindFirstChildOfClass("Tool")
return "at egg, tool=" .. (tool and tool.Name or "none")
"""

FIRE_OBSERVE = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local landed = 0
local ev = rs:FindFirstChild("EggHitLanded")
if ev and ev:IsA("RemoteEvent") then
  ev.OnClientEvent:Connect(function() landed = landed + 1 end)
end
local list = getgenv().__farmEggList
local part = nil
for _, path in ipairs(list) do
  local ok, inst = pcall(function()
    local node = game
    for seg in string.gmatch(path, "[^%.]+") do node = node[seg] end
    return node
  end)
  if ok and inst and inst.Parent then part = inst break end
end
if not part then return "egg gone" end
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
local c0 = cash()
for i = 1, 5 do
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(part) end)
  task.wait(1.5)
end
local c1 = cash()
return string.format("cash=%s->%s landed=%d", tostring(c0), tostring(c1), landed)
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        for label, code in (("scan", SCAN), ("move", MOVE_EQUIP), ("fire", FIRE_OBSERVE)):
            try:
                out = await mcp.call_tool(
                    "get-data-by-code", {"code": code, "timeout": 60000}
                )
            except Exception as exc:
                out = f"FAILED: {type(exc).__name__}: {exc}"
            print(f"=== {label} ===")
            print((out or "")[:800])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
