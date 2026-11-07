import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local out = {}
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" and #txt > 0 and #txt < 60 then
    if txt == "Steal after kill" or txt == "Evade guards" or txt == "Auto farm eggs" or txt == "Idle" or string.find(txt, "v3.0", 1, true) or string.find(txt, "Bindings:", 1, true) then
      out[#out+1] = txt
    end
  end
end
return table.concat(out, " || ")
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
        print((out or "")[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
