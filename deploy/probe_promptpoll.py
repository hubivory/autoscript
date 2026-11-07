import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local n = 0
local sample = {}
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("ProximityPrompt") and d.Name == "StealPrompt" and d.Enabled then
    n = n + 1
    if #sample < 3 then sample[#sample+1] = tostring(d.ObjectText):sub(1, 40) end
  end
end
return n .. "|" .. table.concat(sample, "~")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        for i in range(8):
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": Q, "timeout": 30000})
                print(f"t{i}: {(out or '')[:400]}", flush=True)
            except Exception as exc:
                print(f"t{i} FAILED: {exc}", flush=True)
            await asyncio.sleep(15)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
