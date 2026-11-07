import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local root = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
local me = root and root.Position or Vector3.new(0,0,0)
local anchor = Workspace:FindFirstChild("PromptAnchor")
if anchor then
  local ok, pos = pcall(function() return anchor.Position end)
  if not ok then ok, pos = pcall(function() return anchor:GetPivot().Position end) end
  if ok then out[#out+1] = "anchorpos=" .. tostring(pos) .. " medist=" .. math.floor((pos - me).Magnitude) end
  local n = 0
  for _, c in ipairs(anchor:GetChildren()) do n = n + 1 end
  out[#out+1] = "anchorkids=" .. n
end
local targets = {"Akita", "Cuttlefish", "Snail"}
for _, name in ipairs(targets) do
  local found = nil
  for _, d in ipairs(Workspace:GetDescendants()) do
    if d:IsA("Model") and d.Name == name then
      local ok, pos = pcall(function() return d:GetPivot().Position end)
      if ok then found = d:GetFullName() .. " @" .. math.floor((pos - me).Magnitude) break end
    end
  end
  out[#out+1] = name .. "=" .. tostring(found)
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
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
