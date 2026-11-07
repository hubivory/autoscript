import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local out = {}
for _, pname in ipairs({"Base_3", "Base_4"}) do
  local plot = Workspace.Plots:FindFirstChild(pname)
  if plot then
    local pa = plot:FindFirstChild("PlacedAnimals")
    if pa then
      local kids = {}
      for _, c in ipairs(pa:GetChildren()) do kids[#kids+1] = c.Name .. "." .. c.ClassName end
      out[#out+1] = pname .. " PA=[" .. table.concat(kids, "|") .. "]"
    else
      local kids = {}
      for _, c in ipairs(plot:GetChildren()) do kids[#kids+1] = c.Name .. "." .. c.ClassName end
      out[#out+1] = pname .. " kids=[" .. table.concat(kids, "|") .. "]"
    end
  end
end
return table.concat(out, " || ")
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
        print((out or "")[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
