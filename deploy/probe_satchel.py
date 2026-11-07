import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q1 = """
local p = game:GetService("Players").LocalPlayer
local out = {}
for _, k in ipairs({"CarryCount", "SatchelCapacity", "SatchelTier"}) do
  out[#out+1] = k .. "=" .. tostring(p:GetAttribute(k))
end
local rs = game:GetService("ReplicatedStorage")
local sc = rs:FindFirstChild("Shared", true)
local sat = sc and sc:FindFirstChild("SatchelConfig", true)
if sat then
  local ok, src = pcall(function() return decompile(sat) end)
  if ok then
    getgenv().__sat = src
    out[#out+1] = "satlen=" .. #src
  else out[#out+1] = "satdecfail" end
else out[#out+1] = "nosat" end
return table.concat(out, " | ")
"""

Q2 = """
local src = getgenv().__sat or ""
return src:sub(1, 1500)
"""


async def gdc(mcp, code, timeout=90):
    out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    raw = (out or "")
    if '{"' in raw and '",n=' in raw:
        start = raw.find('{"') + 2
        end = raw.find('",n=')
        return raw[start:end]
    return raw[:2500]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        print(await gdc(mcp, Q1), flush=True)
        print(await gdc(mcp, Q2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
