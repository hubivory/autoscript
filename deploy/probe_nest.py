import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

NEST_PROBE = """
local out = {}
local count = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if count >= 30 then break end
  if string.find(string.lower(d.Name), "nest", 1, true) then
    count = count + 1
    local p = d.Parent
    out[#out+1] = d.Name .. "." .. d.ClassName .. " parent=" .. (p and p.Name or "?")
    if d:IsA("Model") or d:IsA("Folder") then
      local kids = d:GetChildren()
      local names = {}
      for i = 1, math.min(8, #kids) do
        names[#names+1] = kids[i].Name .. "." .. kids[i].ClassName
      end
      out[#out+1] = "  kids(" .. #kids .. ")=" .. table.concat(names, ",")
    end
  end
end
return table.concat(out, " | ")
"""

HIT_REMOTES = """
local out = {}
local rs = game:GetService("ReplicatedStorage")
for _, d in ipairs(rs:GetDescendants()) do
  if d:IsA("RemoteEvent") or d:IsA("RemoteFunction") then
    local n = string.lower(d.Name)
    if string.find(n, "egg", 1, true) or string.find(n, "hit", 1, true) or string.find(n, "swing", 1, true) or string.find(n, "bat", 1, true) or string.find(n, "pickaxe", 1, true) then
      out[#out+1] = d.ClassName .. ":" .. d:GetFullName()
    end
  end
end
return #out .. " | " .. table.concat(out, " ; ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        for label, code in (("NESTS", NEST_PROBE), ("HITREMOTES", HIT_REMOTES)):
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {label} ===")
            print((out or "")[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
