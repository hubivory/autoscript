import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

UNLOAD = """
pcall(function()
  local u = getgenv().SnowyStudiosUnload
  if type(u) == "function" then u() end
end)
return "unloaded"
"""

SET_ON = """
local lib = getgenv().__SnowHubAdapter
local flags = lib and lib.Flags
if not flags then return "no flags" end
flags.AutoFarmEggs = true
return "set:" .. tostring(flags.AutoFarmEggs)
"""

STATUS = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" then
    if txt == "Idle" or string.find(txt, "Broke ", 1, true) or string.find(txt, "Failed:", 1, true) or string.find(txt, "No eggs", 1, true) or string.find(txt, "Travel:", 1, true) or string.find(txt, "Eggs: ", 1, true) then
      return txt:sub(1, 110)
    end
  end
end
return "none"
"""

CASH = """
local p = game:GetService("Players").LocalPlayer
return "cash=" .. tostring(p:GetAttribute("Cash"))
"""


async def gdc(mcp, code):
    out = await mcp.call_tool("get-data-by-code", {"code": code})
    lines = (out or "").strip().splitlines()
    raw = lines[-1].strip() if lines else ""
    if raw.startswith('{"') and raw.endswith('",n=1}'):
        return raw[2:-6]
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return raw[:150]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    with open("/tmp/snowy_v2.lua", encoding="utf-8") as handle:
        script = handle.read()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        print("unload:", await gdc(mcp, UNLOAD))
        await asyncio.sleep(2)
        print("loading v2 fresh...")
        await mcp.call_tool("execute", {"code": script})
        await asyncio.sleep(14)
        print("status:", await gdc(mcp, STATUS))
        print("flag:", await gdc(mcp, SET_ON))
        await asyncio.sleep(5)
        print("cash0:", await gdc(mcp, CASH))
        print("status:", await gdc(mcp, STATUS))
        await asyncio.sleep(30)
        print("cash1:", await gdc(mcp, CASH))
        print("status:", await gdc(mcp, STATUS))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
