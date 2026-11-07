import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

SNAP = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local char = p.Character
local held = {}
if char then for _, t in ipairs(char:GetChildren()) do if t:IsA("Tool") then held[#held+1] = t.Name end end end
out[#out+1] = "held=[" .. table.concat(held, ",") .. "]"
local st = {}
for k, v in pairs(p:GetAttributes()) do
  local ks = tostring(k)
  if string.find(ks, "teal", 1, true) or string.find(ks, "arry", 1, true) or string.find(ks, "old", 1, true) then st[#st+1] = ks .. "=" .. tostring(v) end
end
out[#out+1] = "st=[" .. table.concat(st, ",") .. "]"
local ag = Workspace.Build.ZoneBuilds.Zone10:FindFirstChild("AlienGuardian")
if ag then out[#out+1] = "chase=" .. tostring(ag:GetAttribute("ChaseState")) .. " caught=" .. tostring(ag:GetAttribute("CaughtUserId")) end
local n = 0
for _, d in ipairs(Workspace:GetDescendants()) do if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" then n = n + 1 end end
out[#out+1] = "nprompts=" .. n
return table.concat(out, " | ")
"""


async def gdc(mcp, code, timeout=60):
    out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    return (out or "")[:1500]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        print("before:", await gdc(mcp, SNAP), flush=True)
        try:
            r = await mcp.call_tool(
                "fire-proximity-prompt",
                {"path": "Workspace.PromptAnchor.StealPrompt", "holdDuration": 0.5},
            )
            print("fire:", str(r)[:800], flush=True)
        except Exception as exc:
            print(f"FIRE FAILED: {exc}", flush=True)
        await asyncio.sleep(3)
        print("after:", await gdc(mcp, SNAP), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
