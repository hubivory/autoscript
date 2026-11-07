import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

GOLD_PROBE = """
local out = {}
local seen = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if seen >= 6 then break end
  if d:IsA("Model") and string.find(d.Name, "Nest", 1, true) then
    for _, part in ipairs(d:GetChildren()) do
      if part:IsA("BasePart") and seen < 6 then
        seen = seen + 1
        local attrs = part:GetAttributes()
        local keys = {}
        for k, _ in pairs(attrs) do keys[#keys+1] = k end
        out[#out+1] = string.format(
          "nest=%s part=%s color=%s mat=%s attrs=[%s]",
          d.Name, part.Name, tostring(part.Color), tostring(part.Material),
          table.concat(keys, ","))
      end
    end
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
            out = await mcp.call_tool("get-data-by-code", {"code": GOLD_PROBE})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
