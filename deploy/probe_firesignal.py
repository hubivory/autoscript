import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {}
out[#out+1] = "hasfiresignal=" .. tostring(type(firesignal) == "function")
out[#out+1] = "hasfpp=" .. tostring(type(fireproximityprompt) == "function")
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if not root then return table.concat(out, " ") .. " nochar" end
local best, bestd = nil, 1e9
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
    local ok, pos = pcall(function() return d.Parent.Position end)
    if not ok then ok, pos = pcall(function() return d.Parent:GetPivot().Position end) end
    if ok then
      local dist = (pos - root.Position).Magnitude
      if dist < bestd then best, bestd = d, dist end
    end
  end
end
if not best then return table.concat(out, " ") .. " NOPROMPT" end
out[#out+1] = "prompt=" .. tostring(best.ObjectText):gsub("<[^>]+>", ""):sub(1, 36) .. " @" .. math.floor(bestd)
local ok, pos = pcall(function() return best.Parent.Position end)
if not ok then ok, pos = pcall(function() return best.Parent:GetPivot().Position end) end
if ok and bestd > 9 then root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 0)) task.wait(1.2) end
local c0 = p:GetAttribute("Cash")
local an0 = Workspace.Plots.Base_4:GetAttribute("AnimalsPlaced")
pcall(function() firesignal(best.Triggered, p) end)
task.wait(4)
out[#out+1] = "cash=" .. tostring(c0) .. "->" .. tostring(p:GetAttribute("Cash"))
local held = {}
if char then for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
out[#out+1] = "xp=" .. tostring(p:GetAttribute("MasteryXp_Stealing"))
out[#out+1] = "animals=" .. tostring(Workspace.Plots.Base_4:GetAttribute("AnimalsPlaced")) .. " was " .. tostring(an0)
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) end
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
