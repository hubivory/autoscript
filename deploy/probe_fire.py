import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

SETUP = """
local rs = game:GetService("ReplicatedStorage")
local confirmed = rs:FindFirstChild("EggHitConfirmed")
local landed = rs:FindFirstChild("EggHitLanded")
local rejected = rs:FindFirstChild("EggHitRejected")
if confirmed and confirmed:IsA("RemoteEvent") then
  confirmed.OnClientEvent:Connect(function(...) print("[HITCONF]", ...) end)
end
if landed and landed:IsA("RemoteEvent") then
  landed.OnClientEvent:Connect(function(...) print("[HITLAND]", ...) end)
end
if rejected and rejected:IsA("RemoteEvent") then
  rejected.OnClientEvent:Connect(function(...) print("[HITREJ]", ...) end)
end
local p = game:GetService("Players").LocalPlayer
local pp = p.Character:FindFirstChild("HumanoidRootPart").Position
local best, bestd = nil, 1e9
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") and string.find(d.Name, "Nest", 1, true) then
    local ok, pv = pcall(function() return d:GetPivot().Position end)
    if ok then
      local dist = (pv - pp).Magnitude
      if dist < bestd then best, bestd = d, dist end
    end
  end
end
if not best then return "no nest" end
getgenv().__testNest = best
local cash0 = p:FindFirstChild("leaderstats") and p.leaderstats:FindFirstChild("Cash")
getgenv().__cash0 = cash0 and cash0.Value or -1
return "listening nest=" .. best:GetFullName() .. " cash0=" .. tostring(getgenv().__cash0)
"""

FIRE = """
local rs = game:GetService("ReplicatedStorage")
local req = rs:FindFirstChild("EggHitRequest")
if not req then return "no req" end
local nest = getgenv().__testNest
if not nest then return "no saved nest" end
local ok, err = pcall(function() req:FireServer(nest) end)
local p = game:GetService("Players").LocalPlayer
local cash1 = p:FindFirstChild("leaderstats") and p.leaderstats:FindFirstChild("Cash")
cash1 = cash1 and cash1.Value or -1
return "fired=" .. tostring(ok) .. " err=" .. tostring(err) .. " cash=" .. tostring(cash1)
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        print("setup:", (await mcp.call_tool("execute", {"code": SETUP}))[:200])
        await asyncio.sleep(2)
        print("fire:", (await mcp.call_tool("execute", {"code": FIRE}))[:200])
        await asyncio.sleep(6)
        console = await mcp.call_tool(
            "get-console-output", {"limit": 30, "filter": "HIT"}
        )
        print("=== hit lines ===")
        print((console or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
