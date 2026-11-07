import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

SET_FLAG = """
local lib = getgenv().__SnowHubAdapter
if not lib then return "no adapter" end
local flags = lib.Flags
if not flags then return "no flags" end
local f = flags.AutoFarmEggs
if type(f) == "table" then
  if f.Value ~= nil then f.Value = true else return "holder-no-value" end
else
  flags.AutoFarmEggs = true
end
return "set ok"
"""

STATUS_CASH = """
local p = game:GetService("Players").LocalPlayer
local out = {"cash=" .. tostring(p:GetAttribute("Cash"))}
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" then
    if txt == "Idle" or string.find(txt, "Broke ", 1, true) or string.find(txt, "Failed:", 1, true) or string.find(txt, "No eggs", 1, true) or string.find(txt, "Travel:", 1, true) then
      out[#out+1] = "status=" .. txt:sub(1, 100)
      break
    end
  end
end
return table.concat(out, " ")
"""

UNSET_FLAG = """
local lib = getgenv().__SnowHubAdapter
local flags = lib and lib.Flags
if not flags then return "no flags" end
local f = flags.AutoFarmEggs
if type(f) == "table" then
  if f.Value ~= nil then f.Value = false end
else
  flags.AutoFarmEggs = false
end
return "unset ok"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()

        async def probe(code: str) -> str:
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                return f"FAILED: {exc}"
            lines = (out or "").strip().splitlines()
            return lines[-1] if lines else ""

        print("set:", await probe(SET_FLAG))
        print("t0:", await probe(STATUS_CASH))
        await asyncio.sleep(30)
        print("t30:", await probe(STATUS_CASH))
        await asyncio.sleep(30)
        print("t60:", await probe(STATUS_CASH))
        print("unset:", await probe(UNSET_FLAG))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
