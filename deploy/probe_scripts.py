import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

LIST_CLIENT_SCRIPTS = """
local out = {}
local function walk(root, label, depth, budget)
  if depth > 3 or budget[1] <= 0 then return end
  local kids
  local ok, res = pcall(function() return root:GetChildren() end)
  if not ok then return end
  kids = res
  for _, c in ipairs(kids) do
    if budget[1] <= 0 then break end
    if c:IsA("LocalScript") or c:IsA("ModuleScript") then
      budget[1] = budget[1] - 1
      out[#out+1] = label .. "/" .. c:GetFullName()
    elseif depth < 3 then
      walk(c, label, depth + 1, budget)
    end
  end
end
local p = game:GetService("Players").LocalPlayer
walk(p:FindFirstChild("PlayerScripts"), "PS", 0, {15})
walk(p:FindFirstChild("PlayerGui"), "PG", 0, {10})
return table.concat(out, " ; ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": LIST_CLIENT_SCRIPTS})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print("=== scripts ===")
        print((out or "")[:3000])
        target = "Players.SunFrReal.PlayerScripts.Client"
        try:
            src = await mcp.call_tool("get-script-content", {"scriptPath": target})
        except Exception as exc:
            src = f"FAILED: {exc}"
        print("=== decompile test ===")
        print((src or "")[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
