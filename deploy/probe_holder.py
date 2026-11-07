import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

INSPECT = """
local lib = getgenv().__SnowHubAdapter
if not lib then return "no adapter" end
local out = {"lib=" .. tostring(lib)}
local flags = lib.Flags
out[#out+1] = "flags=" .. tostring(flags)
if type(flags) == "table" then
  local f = flags.AutoFarmEggs
  out[#out+1] = "holdertype=" .. type(f)
  if type(f) == "table" then
    local keys = {}
    for k, v in pairs(f) do keys[#keys+1] = tostring(k) .. ":" .. type(v) end
    out[#out+1] = "holderkeys=" .. table.concat(keys, ",")
  else
    out[#out+1] = "holderval=" .. tostring(f)
  end
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": INSPECT})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
