import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {"me=" .. tostring(p.UserId)}
local char = p.Character
local root = char and char:FindFirstChild("HumanoidRootPart")
if root then out[#out+1] = "pos=" .. tostring(root.Position) end
if char then
  local hum = char:FindFirstChildOfClass("Humanoid")
  if hum then out[#out+1] = "hp=" .. tostring(hum.Health) .. "/" .. tostring(hum.MaxHealth) end
end
local bp = {}
for _, t in ipairs(p.Backpack:GetChildren()) do if t:IsA("Tool") then bp[#bp+1] = t.Name end end
out[#out+1] = "pack=[" .. table.concat(bp, ",") .. "]"
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then
  out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) .. " caught=" .. tostring(ag:GetAttribute("CaughtUserId")) .. " pulse=" .. tostring(ag:GetAttribute("CatchPulse"))
  local ok, apos = pcall(function() return ag:GetPivot().Position end)
  if ok and root then out[#out+1] = "gdist=" .. math.floor((apos - root.Position).Magnitude) end
end
out[#out+1] = "cash=" .. tostring(p:GetAttribute("Cash"))
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
