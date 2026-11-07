import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local root = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
if not root then return "no char" end
local out = {}
local found = {}
for _, d in ipairs(Workspace:GetDescendants()) do
  if d:IsA("Model") then
    local n = d.Name
    if string.find(n, "uard", 1, true) or string.find(n, "ecurity", 1, true) then
      local ok, pos = pcall(function() return d:GetPivot().Position end)
      if ok then found[#found+1] = {m = d, dist = (pos - root.Position).Magnitude} end
    end
  end
  if #found >= 6 then break end
end
out[#out+1] = "nguardmodels=" .. #found
for _, e in ipairs(found) do
  local sibs = {}
  local par = e.m.Parent
  if par then
    for _, s in ipairs(par:GetChildren()) do sibs[#sibs+1] = s.Name .. "." .. s.ClassName end
  end
  out[#out+1] = e.m:GetFullName() .. " @" .. math.floor(e.dist) .. " sibs=[" .. table.concat(sibs, ",", 1, math.min(10, #sibs)) .. "]"
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
