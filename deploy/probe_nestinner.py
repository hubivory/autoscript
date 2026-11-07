import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

NEST_INNER = """
local out = {}
local builds = Workspace:FindFirstChild("Build")
out[#out+1] = "hasBuild=" .. tostring(builds ~= nil)
local zones = builds and builds:FindFirstChild("ZoneBuilds")
out[#out+1] = "hasZones=" .. tostring(zones ~= nil)
if zones then
  local znames = {}
  for _, z in ipairs(zones:GetChildren()) do znames[#znames+1] = z.Name end
  out[#out+1] = "zones=" .. table.concat(znames, ",")
end
local n = 0
local withparts = 0
local sample = nil
for _, d in ipairs(Workspace:GetDescendants()) do
  if n >= 4 then break end
  if d:IsA("Model") and string.find(d.Name, "Nest", 1, true) then
    n = n + 1
    local parts = {}
    for _, c in ipairs(d:GetChildren()) do
      parts[#parts+1] = c.Name .. "." .. c.ClassName
    end
    if #parts > 0 then withparts = withparts + 1 end
    if not sample then sample = d:GetFullName() .. " kids=[" .. table.concat(parts, ",") .. "]" end
  end
end
out[#out+1] = "sample=" .. tostring(sample)
out[#out+1] = "withparts=" .. withparts
return table.concat(out, " | ")
"""

DIAG = """
for _, d in ipairs(game:GetService("CoreGui"):GetDescendants()) do
  local ok, txt = pcall(function() return d.Text end)
  if ok and type(txt) == "string" and (string.find(txt, "Remotes:", 1, true) or string.find(txt, "Bindings:", 1, true)) then
    return txt:sub(1, 200)
  end
end
return "no diag"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        for label, code in (("nests", NEST_INNER), ("diag", DIAG)):
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {label} ===")
            print((out or "")[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
