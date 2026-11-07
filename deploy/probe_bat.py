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
local plot = Workspace.Plots:FindFirstChild("Base_3")
if not plot then return "no plot" end
local pa = plot:FindFirstChild("PlacedAnimals")
if not pa then return "no PA" end
local animal = nil
for _, d in ipairs(pa:GetChildren()) do
  if d:IsA("Model") then animal = d break end
end
if not animal then return "no animal" end
out[#out+1] = "animal=" .. animal:GetFullName()
local hum = char:FindFirstChildOfClass("Humanoid")
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Bat" then hum:EquipTool(t) break end
end
task.wait(0.5)
local ok, pos = pcall(function() return animal:GetPivot().Position end)
if not ok then return "no pos" end
root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 2))
task.wait(1)
local bat = rs:FindFirstChild("BatHitRequest")
if bat and bat:IsA("RemoteEvent") then
  pcall(function() bat:FireServer(animal) end)
  task.wait(2)
  out[#out+1] = "batfired"
end
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
local cf = rs:FindFirstChild("CatchFlingRemote")
if cf and cf:IsA("RemoteEvent") then
  pcall(function() cf:FireServer(animal) end)
  task.wait(2)
  local tools2 = {}
  for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then tools2[#tools2+1] = t.Name end end
  out[#out+1] = "afterfling=[" .. table.concat(tools2, ",") .. "]"
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
