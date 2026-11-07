import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local out = {}
for i = 1, 12 do
  local n = 0
  local sample = ""
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
      n = n + 1
      if sample == "" then sample = tostring(d.ObjectText):sub(1, 45) end
    end
  end
  out[#out+1] = n .. (sample ~= "" and ("=" .. sample) or "")
  task.wait(10)
end
return table.concat(out, " ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 150000})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
