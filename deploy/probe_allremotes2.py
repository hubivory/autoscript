import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

HALF = """
local out = {}
local rs = game:GetService("ReplicatedStorage")
for _, d in ipairs(rs:GetDescendants()) do
  if d:IsA("RemoteEvent") or d:IsA("RemoteFunction") then
    local first = string.sub(d.Name, 1, 1)
    if (first >= "___LO___" and first <= "___HI___") then
      out[#out+1] = (d:IsA("RemoteEvent") and "E" or "F") .. ":" .. d.Name
    end
  end
end
table.sort(out)
return table.concat(out, ",")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        for lo, hi in (("A", "M"), ("N", "Z")):
            code = HALF.replace("___LO___", lo).replace("___HI___", hi)
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {lo}-{hi} ===")
            print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
