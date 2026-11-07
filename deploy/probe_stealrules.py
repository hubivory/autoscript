import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local out = {}
local blk = {"CashPerSecond", "OwnerUserId", "AnimalName", "Gender", "WeightBracket", "ClientMoveSpeed", "AnimationBaseWalkSpeed", "PlacedFootSpan", "PlacedHalfSpan", "SizeMult", "WeightKg", "Rarity", "PlacedCelebrateAt"}
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") and (d.Name == "Akita" or d.Name == "Jackalope" or d.Name == "Badger") then
    local t = {}
    for k, v in pairs(d:GetAttributes()) do
      local ks = tostring(k)
      local skip = false
      for _, b in ipairs(blk) do if ks == b then skip = true break end end
      if not skip then t[#t+1] = ks .. "=" .. tostring(v) end
    end
    out[#out+1] = d.Name .. " extra=[" .. table.concat(t, ",") .. "]"
    if #out >= 4 then break end
  end
end
local n = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" then
    n = n + 1
    if n == 1 then
      out[#out+1] = "P maxd=" .. tostring(d.MaxActivationDistance) .. " los=" .. tostring(d.RequiresLineOfSight) .. " hold=" .. tostring(d.HoldDuration) .. " excl=" .. tostring(d.Exclusivity) .. " click=" .. tostring(d.ClickablePrompt) .. " gamepad=" .. tostring(d.GamepadKeyCode) .. " key=" .. tostring(d.KeyboardKeyCode) .. " parent=" .. d.Parent:GetFullName()
    end
  end
end
out[#out+1] = "nprompts=" .. n
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
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
