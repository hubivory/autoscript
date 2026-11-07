import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

Q = """
local p = game:GetService("Players").LocalPlayer
local out = {}
local pa = Workspace.Plots.Base_4:FindFirstChild("PlacedAnimals")
if pa then
  local first = pa:GetChildren()[1]
  if first then
    local t = {}
    for k, v in pairs(first:GetAttributes()) do t[#t+1] = k .. "=" .. tostring(v) end
    out[#out+1] = first.Name .. "=[" .. table.concat(t, ",") .. "]"
  end
end
local keep = {"teal", "arry", "arry", "tolen", "old", "ank", "uard", "hase", "aught", "rison", "oot", "gg", "ot"}
local mine = {}
for k, v in pairs(p:GetAttributes()) do
  local ks = tostring(k)
  for _, pat in ipairs(keep) do
    if string.find(ks, pat, 1, true) then mine[#mine+1] = ks .. "=" .. tostring(v) break end
  end
end
out[#out+1] = "me=[" .. table.concat(mine, ",") .. "]"
local char = p.Character
if char then
  local cm = {}
  for k, v in pairs(char:GetAttributes()) do cm[#cm+1] = tostring(k) .. "=" .. tostring(v) end
  out[#out+1] = "char=[" .. table.concat(cm, ",") .. "]"
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
