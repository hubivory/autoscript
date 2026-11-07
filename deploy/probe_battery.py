import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

BATTERY = """
local rs = game:GetService("ReplicatedStorage")
local log = {}
local function cash()
  local p = game:GetService("Players").LocalPlayer
  local v = p:GetAttribute("Cash")
  return v == nil and -1 or v
end
local events = {}
for _, name in ipairs({"EggHitConfirmed", "EggHitLanded", "EggHitRejected"}) do
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    r.OnClientEvent:Connect(function(a, b)
      events[#events+1] = name .. ":" .. tostring(a) .. "," .. tostring(b)
    end)
  end
end
local p = game:GetService("Players").LocalPlayer
local pp = p.Character:FindFirstChild("HumanoidRootPart").Position
local best, bestd, bestpart = nil, 1e9, nil
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
local part = best:FindFirstChild("p1") or best:FindFirstChild("p2")
if not part then return "no p1/p2 in " .. best:GetFullName() end
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
log[#log+1] = string.format("target=%s dist=%.0f cash0=%s", part:GetFullName(), bestd, tostring(cash()))
for i = 1, 4 do
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.4)
  local ok, err = pcall(function() req:FireServer(part) end)
  log[#log+1] = string.format("hit%d ok=%s cash=%s", i, tostring(ok), tostring(cash()))
  task.wait(1.6)
end
log[#log+1] = "events=[" .. table.concat(events, "|") .. "]"
log[#log+1] = "partparent=" .. tostring(part.Parent and part.Parent.Name or "nil")
return table.concat(log, " ; ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool(
                "get-data-by-code", {"code": BATTERY, "timeout": 60000}
            )
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
