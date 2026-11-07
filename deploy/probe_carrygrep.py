import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
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

GREP = """
local src = getgenv().__src or ""
local out = {}
local pat = "___PAT___"
local i = 1
while #out < 6 do
  local s, e = string.find(src, pat, i, true)
  if not s then break end
  out[#out+1] = src:sub(math.max(1, s - 160), math.min(#src, e + 160))
  i = e + 1
end
return "[[SEP]]" .. table.concat(out, "[[SEP]]")
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
        print(await gdc(mcp, Q.replace("___NAME___", "CarryController")), flush=True)
        for pat in ("CarryCount", "Triggered", "FireServer"):
            try:
                print(f"##### {pat} #####", flush=True)
                print(await gdc(mcp, GREP.replace("___PAT___", pat)), flush=True)
            except Exception as exc:
                print(f"{pat} FAILED: {exc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
