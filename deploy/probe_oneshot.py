import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

ONESHOT = """
local rs = game:GetService("ReplicatedStorage")
local got = {}
local function listen(name, tag)
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    r.OnClientEvent:Connect(function(...) got[#got+1] = tag .. ":" .. tostring(...) end)
  end
end
listen("EggHitConfirmed", "CONF")
listen("EggHitLanded", "LAND")
listen("EggHitRejected", "REJ")
local p = game:GetService("Players").LocalPlayer
local cash0 = p.leaderstats and p.leaderstats:FindFirstChild("Cash")
cash0 = cash0 and cash0.Value or -1
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
if not best then return "no nest nearby" end
local req = rs:FindFirstChild("EggHitRequest")
if not req then return "no req" end
local ok, err = pcall(function() req:FireServer(best) end)
task.wait(5)
local cash1 = p.leaderstats and p.leaderstats:FindFirstChild("Cash")
cash1 = cash1 and cash1.Value or -1
return string.format("fired=%s dist=%.0f cash=%s->%s events=[%s]", tostring(ok), bestd, tostring(cash0), tostring(cash1), table.concat(got, "|"))
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": ONESHOT})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
