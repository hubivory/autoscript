import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

STATUS = """
local out = {}
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" then
    if string.find(txt, "Broke ", 1, true) or string.find(txt, "Failed:", 1, true) or txt == "Idle" or string.find(txt, "No eggs", 1, true) or string.find(txt, "Travel:", 1, true) or string.find(txt, "Scanning", 1, true) or string.find(txt, "Eggs:", 1, true) then
      out[#out+1] = txt:sub(1, 120)
    end
  end
end
local nests = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") and string.find(d.Name, "Nest", 1, true) then nests = nests + 1 end
end
out[#out+1] = "nestmodels=" .. nests
return table.concat(out, " || ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": STATUS})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
