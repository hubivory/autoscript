import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

CASH = """
local p = game:GetService("Players").LocalPlayer
return "cash=" .. tostring(p:GetAttribute("Cash"))
"""

STATUS = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" then
    if string.find(txt, "Broke ", 1, true) or string.find(txt, "Failed:", 1, true) or txt == "Idle" or string.find(txt, "No eggs", 1, true) or string.find(txt, "Travel:", 1, true) then
      return txt:sub(1, 150)
    end
  end
end
return "no status"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        for label, code in (("cash", CASH), ("status", STATUS)):
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"{label}: {(out or '')[-200:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
