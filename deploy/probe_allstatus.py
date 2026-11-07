import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

ALL_STATUS = """
local out = {}
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" and #txt > 0 and #txt < 120 then
    if txt == "Idle" or string.find(txt, "Broke ", 1, true) or string.find(txt, "Failed:", 1, true) or string.find(txt, "No eggs", 1, true) or string.find(txt, "Travel:", 1, true) or string.find(txt, "Eggs: ", 1, true) or string.find(txt, "Scanning", 1, true) or string.find(txt, "Throttled", 1, true) or string.find(txt, "disabled after", 1, true) then
      out[#out+1] = txt
    end
  end
end
local lib = getgenv().__SnowHubAdapter
local flags = lib and lib.Flags
out[#out+1] = "FLAG=" .. tostring(flags and flags.AutoFarmEggs)
return table.concat(out, " || ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": ALL_STATUS})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
