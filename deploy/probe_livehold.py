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
local prompt = nil
for i = 1, 20 do
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
      prompt = d
      break
    end
  end
  if prompt then break end
  task.wait(3)
end
if not prompt then return "NOLIVE" end
out[#out+1] = "live=" .. tostring(prompt.ObjectText):gsub("<[^>]+>", ""):sub(1, 44)
local ok, pos = pcall(function() return prompt.Parent.Position end)
if not ok then ok, pos = pcall(function() return prompt.Parent:GetPivot().Position end) end
if not ok then return "NOPOS" end
root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 0))
task.wait(1.2)
local vim = game:GetService("VirtualInputManager")
local c0 = p:GetAttribute("Cash")
local xp0 = p:GetAttribute("MasteryXp_Stealing")
vim:SendKeyEvent(true, Enum.KeyCode.E, false, game)
task.wait(0.7)
vim:SendKeyEvent(false, Enum.KeyCode.E, false, game)
task.wait(3)
out[#out+1] = "cash=" .. tostring(c0) .. "->" .. tostring(p:GetAttribute("Cash"))
out[#out+1] = "xp=" .. tostring(xp0) .. "->" .. tostring(p:GetAttribute("MasteryXp_Stealing"))
local held = {}
if char then for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
local plot = Workspace.Plots:FindFirstChild("Base_4")
out[#out+1] = "animals=" .. tostring(plot and plot:GetAttribute("AnimalsPlaced"))
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then
  local ok2, gpos = pcall(function() return ag:GetPivot().Position end)
  if ok2 then out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) .. " gdist=" .. math.floor((gpos - root.Position).Magnitude) end
end
root.CFrame = CFrame.new(home + Vector3.new(0, 3, 0))
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 115000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
