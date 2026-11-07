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
if not best then return "NOPROMPT" end
local ok, pos = pcall(function() return best.Parent.Position end)
if not ok then ok, pos = pcall(function() return best.Parent:GetPivot().Position end) end
if not ok then return "NOPOS" end
out[#out+1] = "obj=" .. tostring(best.ObjectText):sub(1, 80)
out[#out+1] = "at=" .. math.floor(bestd) .. " maxd=" .. tostring(best.MaxActivationDistance)
out[#out+1] = "pparent=" .. best.Parent:GetFullName()
root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 0))
task.wait(1.5)
local c0 = p:GetAttribute("Cash")
local fpp = fireproximityprompt or fire_proximity_prompt
if type(fpp) ~= "function" then return "NOFPP" end
pcall(function() fpp(best) end)
task.wait(3)
out[#out+1] = "cash=" .. tostring(c0) .. "->" .. tostring(p:GetAttribute("Cash"))
local held = {}
if char then for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
local st = {}
for k, v in pairs(p:GetAttributes()) do
  local ks = tostring(k)
  if string.find(ks, "teal", 1, true) or string.find(ks, "arry", 1, true) or string.find(ks, "old", 1, true) or string.find(ks, "aught", 1, true) then st[#st+1] = ks .. "=" .. tostring(v) end
end
out[#out+1] = "st=[" .. table.concat(st, ",") .. "]"
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then
  local ok2, apos = pcall(function() return ag:GetPivot().Position end)
  if ok2 then out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) .. " gdist=" .. math.floor((apos - root.Position).Magnitude) end
end
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
