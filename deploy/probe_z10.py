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
local z10 = Workspace.Build.ZoneBuilds:FindFirstChild("Zone10")
if not z10 then return "no z10" end
local ef = z10:FindFirstChild("Eggs")
if ef then
  local kids = {}
  for _, c in ipairs(ef:GetChildren()) do kids[#kids+1] = c.Name .. "." .. c.ClassName end
  out[#out+1] = "eggs=[" .. table.concat(kids, "|") .. "]"
end
local ag = z10:FindFirstChild("AlienGuardian")
if ag then
  local function attrs(inst)
    local t = {}
    for k, v in pairs(inst:GetAttributes()) do t[#t+1] = k .. "=" .. tostring(v) end
    return "[" .. table.concat(t, ",") .. "]"
  end
  out[#out+1] = "ag=" .. ag:GetFullName() .. " " .. attrs(ag)
  local ok, pos = pcall(function() return ag:GetPivot().Position end)
  if ok then
    out[#out+1] = "agdist=" .. math.floor((pos - root.Position).Magnitude)
    root.CFrame = CFrame.new(pos + Vector3.new(0, 5, 60))
    task.wait(2)
    local ok2, pos2 = pcall(function() return ag:GetPivot().Position end)
    if ok2 then out[#out+1] = "agmoved=" .. tostring((pos2 - pos).Magnitude > 1) end
  end
  local parts = {}
  for _, d in ipairs(ag:GetDescendants()) do
    if d:IsA("ProximityPrompt") or d:IsA("ClickDetector") then parts[#parts+1] = d.ClassName .. " in " .. d.Parent.Name end
    if #parts >= 5 then break end
  end
  out[#out+1] = "agprompts=[" .. table.concat(parts, ",") .. "]"
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
