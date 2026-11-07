import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if not root then return "no char" end
local home = root.Position
local akita = nil
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") and d.Name == "Akita" then akita = d break end
end
if not akita then return "NOAKITA" end
local ok, apos = pcall(function() return akita:GetPivot().Position end)
if not ok then return "NOPOS" end
out[#out+1] = "akita=" .. akita:GetFullName()
root.CFrame = CFrame.new(apos + Vector3.new(0, 4, 4))
task.wait(2)
local found = {}
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") then
    local ok2, pos2 = pcall(function() return d.Parent.Position end)
    if not ok2 then ok2, pos2 = pcall(function() return d.Parent:GetPivot().Position end) end
    if ok2 and (pos2 - apos).Magnitude < 40 then
      found[#found+1] = d.Name .. "|" .. tostring(d.ActionText) .. "|" .. tostring(d.ObjectText):gsub("<[^>]+>", ""):sub(1,30) .. "|en=" .. tostring(d.Enabled) .. "@" .. math.floor((pos2 - apos).Magnitude)
    end
    if #found >= 8 then break end
  end
end
out[#out+1] = "near=[" .. table.concat(found, " // ") .. "]"
local c0 = p:GetAttribute("Cash")
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
    local ok2, pos2 = pcall(function() return d.Parent.Position end)
    if not ok2 then ok2, pos2 = pcall(function() return d.Parent:GetPivot().Position end) end
    if ok2 and (pos2 - apos).Magnitude < 15 then
      pcall(function() firesignal(d.Triggered, p) end)
      out[#out+1] = "fired-local"
      break
    end
  end
end
task.wait(4)
out[#out+1] = "cash=" .. tostring(c0) .. "->" .. tostring(p:GetAttribute("Cash"))
out[#out+1] = "carry=" .. tostring(p:GetAttribute("CarryCount"))
out[#out+1] = "xp=" .. tostring(p:GetAttribute("MasteryXp_Stealing"))
root.CFrame = CFrame.new(home + Vector3.new(0, 3, 0))
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 90000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
