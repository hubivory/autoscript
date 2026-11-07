import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local out = {}
local names = {}
local total = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
    total = total + 1
    if #names < 25 then
      local txt = tostring(d.ObjectText):gsub("<[^>]+>", "")
      names[#names+1] = txt:sub(1, 28)
    end
  end
end
out[#out+1] = "total=" .. total
out[#out+1] = "board=[" .. table.concat(names, "|") .. "]"
return table.concat(out, " ")
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
