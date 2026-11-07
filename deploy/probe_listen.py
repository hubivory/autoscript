import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

LISTEN = """
local rs = game:GetService("ReplicatedStorage")
getgenv().__hitlog = {}
local function listen(name)
  local r = rs:FindFirstChild(name)
  if r and r:IsA("RemoteEvent") then
    r.OnClientEvent:Connect(function(...)
      local args = {...}
      local parts = {}
      for i, v in ipairs(args) do
        local ok, s = pcall(function()
          if typeof(v) == "Instance" then return v.ClassName .. ":" .. v:GetFullName()
          else return tostring(v) end
        end)
        parts[#parts+1] = ok and s or "?"
      end
      table.insert(getgenv().__hitlog, name .. "(" .. table.concat(parts, ", ") .. ")")
      print("[HITR " .. name .. "] " .. table.concat(parts, " | "))
    end)
    return "ok:" .. name
  end
  return "missing:" .. name
end
local a = listen("EggHitConfirmed")
local b = listen("EggHitLanded")
local c = listen("EggHitRejected")
return a .. " " .. b .. " " .. c
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": LISTEN})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:800])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
