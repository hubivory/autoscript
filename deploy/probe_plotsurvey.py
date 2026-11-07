import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local out = {}
for _, plot in ipairs(Workspace.Plots:GetChildren()) do
  local nan, negg, grd = 0, {}, {}
  for _, d in ipairs(plot:GetDescendants()) do
    if d:IsA("Model") and (d.Name == "Chicken" or d.Name == "Cat" or d.Name == "Dog" or string.find(d.Name, "nimal", 1, true)) then nan = nan + 1 end
    if d:IsA("BasePart") and (d.Name == "Egg" or d.Name == "Gold") then negg[#negg+1] = d.Parent.Name end
    if d:IsA("Model") then
      local n = d.Name
      if n == "Guard" or string.find(n, "uard", 1, true) or string.find(n, "ecurity", 1, true) or string.find(n, "efender", 1, true) then grd[#grd+1] = n end
    end
    if d:IsA("ProximityPrompt") or d:IsA("ClickDetector") then negg[#negg+1] = "PROMPT:" .. d.Parent.Name end
  end
  out[#out+1] = plot.Name .. " an=" .. nan .. " eggs={" .. table.concat(negg, ",") .. "} g={" .. table.concat(grd, ",") .. "}"
end
return table.concat(out, " | ")
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
