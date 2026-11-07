import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

DECOMP = """
local p = game:GetService("Players").LocalPlayer
local client = p.PlayerScripts:FindFirstChild("Client")
local target = nil
if client then
  for _, d in ipairs(client:GetDescendants()) do
    if d:IsA("ModuleScript") and d.Name == "___NAME___" then target = d break end
  end
end
if not target then return "NOMOD" end
local ok, src = pcall(function() return decompile(target) end)
if not ok then return "DECFAIL" end
getgenv().__src = src
return "len=" .. #src
"""

SLICE = """
local src = getgenv().__src or ""
return src:sub(___A___, ___B___)
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
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=240) as mcp:
        await mcp.list_tools()
        for name in ("CarryController", "CatchFlingController", "StealPromptVisibilityController"):
            try:
                info = await gdc(mcp, DECOMP.replace("___NAME___", name))
                print(f"=== {name}: {info[:60]} ===", flush=True)
                try:
                    length = int(info.split("len=")[1].split()[0])
                except Exception:
                    length = 0
                pos = 1
                while pos <= length and pos < 12000:
                    chunk = await gdc(mcp, SLICE.replace("___A___", str(pos)).replace("___B___", str(pos + 1400)))
                    print(chunk, flush=True)
                    pos += 1401
            except Exception as exc:
                print(f"{name} FAILED: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
