import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

BUILD_PROBE = """
local out = {}
local plots = Workspace:FindFirstChild("Plots")
local first = plots and plots:GetChildren()[1]
if first then
  local build = first:FindFirstChild("Build")
  if build then
    local kids = build:GetChildren()
    out[#out+1] = "buildkids=" .. #kids
    for i = 1, math.min(12, #kids) do
      out[#out+1] = " b=" .. kids[i].Name .. "." .. kids[i].ClassName
    end
  else
    out[#out+1] = "no Build"
  end
end
local meshes = 0
for _, d in ipairs(Workspace:GetDescendants()) do
  if meshes >= 15 then break end
  if d:IsA("MeshPart") or (d:IsA("BasePart") and d.Name ~= "Part" and d.Name ~= "SpawnPoint" and d.Name ~= "Hitbox") then
    meshes = meshes + 1
    local p = d.Parent
    out[#out+1] = "mesh=" .. d.Name .. "." .. d.ClassName .. " parent=" .. (p and p.Name or "?")
  end
end
return table.concat(out, " | ")
"""

ALL_REMOTES = """
local out = {}
local rs = game:GetService("ReplicatedStorage")
for _, d in ipairs(rs:GetDescendants()) do
  if d:IsA("RemoteEvent") or d:IsA("RemoteFunction") then
    out[#out+1] = d.ClassName .. ":" .. d:GetFullName()
  end
end
return #out .. " total | " .. table.concat(out, " ; ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        for label, code in (("BUILD", BUILD_PROBE), ("REMOTES", ALL_REMOTES)):
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {label} ===")
            print((out or "")[:3500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
