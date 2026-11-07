import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

RECON = """
local p = game:GetService("Players").LocalPlayer
local root = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
if not root then return "no char" end
local out = {"me=" .. tostring(root.Position)}
local plots = Workspace:FindFirstChild("Plots")
if not plots then return "no Plots container" end
local list = {}
for _, plot in ipairs(plots:GetChildren()) do
  local ok, pos = pcall(function() return plot:GetPivot().Position end)
  if ok then list[#list+1] = {plot = plot, dist = (pos - root.Position).Magnitude} end
end
table.sort(list, function(a, b) return a.dist < b.dist end)
out[#out+1] = "nplots=" .. #list
for i = 1, math.min(2, #list) do
  local e = list[i]
  out[#out+1] = "plot" .. i .. "=" .. e.plot.Name .. "@" .. math.floor(e.dist)
  local animals, eggs, guards, prompts = {}, {}, {}, {}
  for _, d in ipairs(e.plot:GetDescendants()) do
    local n = d.Name
    if d:IsA("Model") and (string.find(n, "uard", 1, true) or string.find(n, "Guard", 1, true)) then guards[#guards+1] = n end
    if d:IsA("ProximityPrompt") then prompts[#prompts+1] = n .. " in " .. d.Parent.Name end
    if d:IsA("ClickDetector") then prompts[#prompts+1] = "click in " .. d.Parent.Name end
    if d:IsA("Model") and (n == "Chicken" or n == "Cat" or n == "Dog" or string.find(n, "Animal", 1, true) or string.find(n, "Pet", 1, true)) then animals[#animals+1] = n end
    if d:IsA("BasePart") and (n == "Egg" or n == "Gold") then eggs[#eggs+1] = n .. " in " .. d.Parent.Name end
  end
  local function head(t)
    if #t == 0 then return "" end
    return table.concat(t, ",", 1, math.min(6, #t))
  end
  out[#out+1] = " animals=[" .. head(animals) .. "]n=" .. #animals
  out[#out+1] = " eggs=[" .. head(eggs) .. "]n=" .. #eggs
  out[#out+1] = " guards=[" .. head(guards) .. "]"
  out[#out+1] = " prompts=[" .. head(prompts) .. "]n=" .. #prompts
end
return table.concat(out, " | ")
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        try:
            out = await mcp.call_tool("get-data-by-code", {"code": RECON})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2200])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
