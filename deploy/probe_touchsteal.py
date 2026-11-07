import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

TOUCH_STEAL = """
local p = game:GetService("Players").LocalPlayer
local rs = game:GetService("ReplicatedStorage")
local out = {}
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if not root then return "no char" end
local plots = Workspace:FindFirstChild("Plots")
if not plots then return "no plots" end
local function ownerOf(plot)
  for _, a in ipairs({"Owner", "OwnerName", "PlayerName", "OwnerId"}) do
    local v = plot:GetAttribute(a)
    if v ~= nil then return tostring(v) end
  end
  return "?"
end
local list = {}
for _, plot in ipairs(plots:GetChildren()) do
  local ok, pos = pcall(function() return plot:GetPivot().Position end)
  if ok then list[#list+1] = {plot = plot, dist = (pos - root.Position).Magnitude} end
end
table.sort(list, function(a, b) return a.dist < b.dist end)
local me = tostring(p.UserId) .. "|" .. p.Name .. "|" .. p.DisplayName
out[#out+1] = "me=" .. me
local target = nil
for _, e in ipairs(list) do
  local own = ownerOf(e.plot)
  out[#out+1] = e.plot.Name .. " owner=" .. own .. " @" .. math.floor(e.dist)
  if not target then
    local isMine = string.find(own, p.Name, 1, true) or string.find(own, tostring(p.UserId), 1, true)
    if not isMine then
      for _, d in ipairs(e.plot:GetDescendants()) do
        if d:IsA("Model") and (d.Name == "Chicken" or d.Name == "Cat" or d.Name == "Dog") then
          target = d
          out[#out+1] = "target=" .. d:GetFullName()
          break
        end
      end
    end
  end
  if target then break end
end
if not target then return table.concat(out, " ") .. " NOFOREIGNTARGET" end
local ok, tpos = pcall(function() return target:GetPivot().Position end)
if not ok then return "no target pos" end
root.CFrame = CFrame.new(tpos + Vector3.new(0, 3, 2))
task.wait(2.5)
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
local drop = rs:FindFirstChild("DropCarriedRemote")
if drop and drop:IsA("RemoteEvent") then
  pcall(function() drop:FireServer() end)
  task.wait(1)
  local tools2 = {}
  for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then tools2[#tools2+1] = t.Name end end
  out[#out+1] = "afterdrop=[" .. table.concat(tools2, ",") .. "]"
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": TOUCH_STEAL, "timeout": 60000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
