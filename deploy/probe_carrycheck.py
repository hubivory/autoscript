import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {}
out[#out+1] = "carry0=" .. tostring(p:GetAttribute("CarryCount"))
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if not root then return table.concat(out, " ") end
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
local ok, pos = pcall(function() return best.Parent.Position end)
if not ok then ok, pos = pcall(function() return best.Parent:GetPivot().Position end) end
if ok and bestd > 9 then root.CFrame = CFrame.new(pos + Vector3.new(0, 3, 0)) task.wait(1.2) end
pcall(function() firesignal(best.Triggered, p) end)
task.wait(4)
out[#out+1] = "carry1=" .. tostring(p:GetAttribute("CarryCount"))
local kids = {}
if char then for _, c in ipairs(char:GetChildren()) do kids[#kids+1] = c.Name .. "." .. c.ClassName end end
out[#out+1] = "char=[" .. table.concat(kids, ","):sub(1, 400) .. "]"
local welds = {}
if char then for _, d in ipairs(char:GetDescendants()) do
  if d:IsA("Weld") or d:IsA("Motor6D") or d:IsA("WeldConstraint") then welds[#welds+1] = d.Name .. ":" .. d.ClassName end
  if #welds >= 8 then break end
end end
out[#out+1] = "welds=[" .. table.concat(welds, ",") .. "]"
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
