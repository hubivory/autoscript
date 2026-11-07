import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

TAIL = """
local src = getgenv().__src or ""
return "tail=[" .. src:sub(1001) .. "]"
"""

SIBS = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local client = p.PlayerScripts:FindFirstChild("Client")
if client then
  for _, d in ipairs(client:GetDescendants()) do
    if d:IsA("ModuleScript") then
      local n = string.lower(d.Name)
      if string.find(n, "teal", 1, true) or string.find(n, "arry", 1, true) or string.find(n, "uard", 1, true) or string.find(n, "rompt", 1, true) or string.find(n, "lot", 1, true) or string.find(n, "ank", 1, true) or string.find(n, "atch", 1, true) or string.find(n, "ling", 1, true) then
        out[#out+1] = d.Name
      end
    end
  end
end
table.sort(out)
return table.concat(out, ",")
"""


async def gdc(mcp, code, timeout=90):
    out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    return (out or "")[:2500]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        for label, code in (("tail", TAIL), ("sibs", SIBS)):
            try:
                print(f"=== {label} ===", flush=True)
                print(await gdc(mcp, code), flush=True)
            except Exception as exc:
                print(f"{label} FAILED: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
