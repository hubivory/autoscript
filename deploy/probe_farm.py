import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

EGG_PROBE = """
local out = {}
local plots = Workspace:FindFirstChild("Plots")
if not plots then return "no Plots" end
local n = 0
for _, plot in ipairs(plots:GetChildren()) do
  for _, d in ipairs(plot:GetDescendants()) do
    if d:IsA("BasePart") and (d.Name == "Egg" or d.Name == "Gold") then
      n = n + 1
      if n == 1 then
        local kids = {}
        for _, c in ipairs(d:GetChildren()) do
          kids[#kids+1] = c.ClassName .. ":" .. c.Name
        end
        local model = d.Parent
        local mkids = {}
        if model and model ~= plot then
          for _, c in ipairs(model:GetChildren()) do
            if c:IsA("ClickDetector") or c:IsA("ProximityPrompt") then
              mkids[#mkids+1] = c.ClassName .. ":" .. c.Name
            end
          end
        end
        out[#out+1] = "egg=" .. d:GetFullName() .. " kids=[" .. table.concat(kids, ",") .. "] modelclick=[" .. table.concat(mkids, ",") .. "]"
      end
      if n >= 40 then break end
    end
  end
  if n >= 40 then break end
end
return "eggs=" .. n .. " " .. table.concat(out, " | ")
"""

REMOTE_PROBE = """
local out = {}
local function scan(root, label)
  local found = root and root:GetDescendants() or {}
  for _, d in ipairs(found) do
    if d:IsA("RemoteEvent") or d:IsA("RemoteFunction") then
      local n = string.lower(d.Name)
      if string.find(n, "break") or string.find(n, "swing") or string.find(n, "click") or string.find(n, "damage") or string.find(n, "hit") or string.find(n, "mine") or string.find(n, "attack") then
        out[#out+1] = label .. "/" .. d:GetFullName()
      end
    end
  end
end
scan(game:GetService("ReplicatedStorage"), "RS")
scan(Workspace, "WS")
return #out .. " remotes: " .. table.concat(out, " ; ")
"""

TOOL_PROBE = """
local out = {}
for _, t in ipairs(game:GetService("Players").LocalPlayer.Backpack:GetChildren()) do
  if t:IsA("Tool") then
    out[#out+1] = t.Name
  end
end
local char = game:GetService("Players").LocalPlayer.Character
if char then
  local tool = char:FindFirstChildOfClass("Tool")
  if tool then out[#out+1] = "equipped:" .. tool.Name end
end
return table.concat(out, ",")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=90) as mcp:
        await mcp.list_tools()
        for label, code in (("EGGS", EGG_PROBE), ("REMOTES", REMOTE_PROBE), ("TOOLS", TOOL_PROBE)):
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"=== {label} ===")
            print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
