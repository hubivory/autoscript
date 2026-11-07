import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

OWNERS = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local plots = Workspace:FindFirstChild("Plots")
if not plots then return "no plots" end
for _, plot in ipairs(plots:GetChildren()) do
  local bits = {}
  for k, v in pairs(plot:GetAttributes()) do bits[#bits+1] = k .. "=" .. tostring(v) end
  local ck = {}
  for _, c in ipairs(plot:GetChildren()) do
    if c:IsA("ObjectValue") and (c.Name == "Owner" or string.find(c.Name, "wner", 1, true)) then
      ck[#ck+1] = c.Name .. "->" .. (c.Value and c.Value.Name or "nil")
    end
    if (c:IsA("StringValue") or c:IsA("IntValue")) and (c.Name == "Owner" or string.find(c.Name, "wner", 1, true)) then
      ck[#ck+1] = c.Name .. "=" .. tostring(c.Value)
    end
  end
  out[#out+1] = plot.Name .. " attrs=[" .. table.concat(bits, ",") .. "] own=[" .. table.concat(ck, ",") .. "]"
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": OWNERS})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
