import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

LIST = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local function walk(root, depth)
  if depth > 3 or #out > 30 then return end
  for _, c in ipairs(root:GetChildren()) do
    if c:IsA("LocalScript") or c:IsA("ModuleScript") then
      out[#out+1] = c.ClassName .. ":" .. c:GetFullName()
    end
    if #out <= 30 and depth < 3 and not c:IsA("BasePart") then
      pcall(function() walk(c, depth + 1) end)
    end
  end
end
walk(p:FindFirstChild("PlayerScripts"), 0)
walk(p:FindFirstChild("PlayerGui"), 0)
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": LIST})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
