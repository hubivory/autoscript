import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q_DROPS = """
local p = game:GetService("Players").LocalPlayer
local root = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
local drops = {}
if root then
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("BasePart") or d:IsA("Model") then
      local n = d.Name
      if string.find(n, "Drop", 1, true) or string.find(n, "Loot", 1, true) or string.find(n, "Gem", 1, true) or string.find(n, "Steal", 1, true) or string.find(n, "Carry", 1, true) or string.find(n, "Carried", 1, true) then
        local ok, pos = pcall(function()
          if d:IsA("Model") then return d:GetPivot().Position else return d.Position end
        end)
        if ok and (pos - root.Position).Magnitude < 100 then drops[#drops+1] = n .. "@" .. math.floor((pos - root.Position).Magnitude) end
        if #drops >= 8 then break end
      end
    end
  end
end
return "drops=[" .. table.concat(drops, "|") .. "]"
"""

Q_STEAL = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local out = {}
for _, name in ipairs({"EggGemDropRemote", "CatchFlingRemote", "DropCarriedRemote", "PlaceAnimalRemote", "AnimalBankedRemote", "BatHitRequest", "GuardMorphRemote", "FollowPetRemote"}) do
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    local before = cash()
    pcall(function() r:FireServer() end)
    task.wait(0.8)
    local after = cash()
    out[#out+1] = name .. ":" .. tostring(after - before)
  else
    out[#out+1] = name .. "=x"
  end
end
return table.concat(out, " ")
"""

Q_CONF = """
local conf = getgenv().__confirms or {}
local tail = {}
for i = math.max(1, #conf - 5), #conf do tail[#tail+1] = conf[i] end
return "n=" .. #conf .. " tail=[" .. table.concat(tail, " ") .. "]"
"""


async def gdc(mcp, code, timeout=60):
    out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    return (out or "")[:2200]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        for label, code in (("drops", Q_DROPS), ("steal", Q_STEAL), ("conf", Q_CONF)):
            try:
                print(f"=== {label} ===", flush=True)
                print(await gdc(mcp, code), flush=True)
            except Exception as exc:
                print(f"{label} FAILED: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
