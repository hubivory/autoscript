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
local pa = Workspace.Plots.Base_3:FindFirstChild("PlacedAnimals")
local animal = pa and pa:FindFirstChild("Chicken")
if not animal then return "no chicken" end
local function attrs(inst)
  local t = {}
  for k, v in pairs(inst:GetAttributes()) do t[#t+1] = k .. "=" .. tostring(v) end
  return "[" .. table.concat(t, ",") .. "]"
end
out[#out+1] = "before=" .. attrs(animal)
local hum = char:FindFirstChildOfClass("Humanoid")
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Bat" then hum:EquipTool(t) break end
end
task.wait(0.5)
local ok, pos = pcall(function() return animal:GetPivot().Position end)
if ok then root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 3)) end
task.wait(1)
local bat = rs:FindFirstChild("BatHitRequest")
for i = 1, 10 do
  if bat then pcall(function() bat:FireServer(animal) end) end
  task.wait(1.2)
end
out[#out+1] = "after=" .. attrs(animal)
local tools = {}
for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then tools[#tools+1] = t.Name end end
out[#out+1] = "held=[" .. table.concat(tools, ",") .. "]"
local gd = 1e9
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") and string.find(d.Name, "uard", 1, true) then
    local ok2, pos2 = pcall(function() return d:GetPivot().Position end)
    if ok2 then gd = math.min(gd, (pos2 - root.Position).Magnitude) end
  end
end
out[#out+1] = "guard=" .. math.floor(gd)
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
