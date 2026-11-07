import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

OUT = "/tmp/steal_discovery.jsonl"
POLL_S = 30
MAX_WAIT_S = 45 * 60

BASELINE = """
local p = game:GetService("Players").LocalPlayer
return "cash=" .. tostring(p:GetAttribute("Cash"))
"""

BREAK_VERIFY = """
local rs = game:GetService("ReplicatedStorage")
local p = game:GetService("Players").LocalPlayer
local function cash() local v = p:GetAttribute("Cash") return v == nil and -1 or v end
local pp = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
if not pp then return "no char" end
local best, bestd = nil, 1e9
local builds = Workspace:FindFirstChild("Build")
local zones = builds and builds:FindFirstChild("ZoneBuilds")
if not zones then return "no zones" end
for _, zone in ipairs(zones:GetChildren()) do
  local ef = zone:FindFirstChild("Eggs")
  local roots = {}
  if ef then roots = {ef} else roots = {zone} end
  for _, root in ipairs(roots) do
    for _, d in ipairs(root:GetDescendants()) do
      if d:IsA("BasePart") and d.Parent and (d.Name == "Egg" or string.find(d.Parent.Name, "Nest", 1, true)) then
        local ok, pv = pcall(function() return d.Position end)
        if ok then
          local dist = (pv - pp.Position).Magnitude
          if dist < bestd then best, bestd = d, dist end
        end
      end
    end
  end
end
if not best then return "no egg" end
local swing = rs:FindFirstChild("MasteryPickaxeSwing")
local req = rs:FindFirstChild("EggHitRequest")
if not req then return "no req" end
local c0 = cash()
for i = 1, 3 do
  if swing then pcall(function() swing:FireServer() end) end
  task.wait(0.3)
  pcall(function() req:FireServer(best) end)
  task.wait(1.2)
end
return string.format("hits=3 cash=%s->%s", tostring(c0), tostring(cash()))
"""

CENSUS = """
local out = {}
for _, d in ipairs(game:GetService("ReplicatedStorage"):GetDescendants()) do
  if d:IsA("RemoteEvent") or d:IsA("RemoteFunction") then
    local first = string.sub(d.Name, 1, 1)
    if (first >= "___LO___" and first <= "___HI___") then
      out[#out+1] = (d:IsA("RemoteEvent") and "E" or "F") .. ":" .. d.Name
    end
  end
end
table.sort(out)
return table.concat(out, ",")
"""


def log(obj):
    line = json.dumps(obj)
    with open(OUT, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


async def gdc(mcp, code, timeout=60):
    try:
        out = await mcp.call_tool("get-data-by-code", {"code": code, "timeout": timeout * 1000})
    except Exception as exc:
        return f"FAILED: {exc}"
    return (out or "")[:2500]


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    log({"event": "watcher_start", "t": time.time()})
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=180) as mcp:
        await mcp.list_tools()
        waited = 0
        info = None
        while waited < MAX_WAIT_S:
            try:
                info = await mcp.call_tool("get-game-info", {})
                if info and "No Roblox client" not in str(info):
                    break
            except Exception as exc:
                info = f"ERR {exc}"
            await asyncio.sleep(POLL_S)
            waited += POLL_S
        log({"event": "client", "info": str(info)[:300]})
        if not info or "No Roblox client" in str(info):
            log({"event": "timeout_no_client"})
            return 2
        if "Break and Steal" not in str(info) and "11432693441783" not in str(info):
            log({"event": "wrong_game"})
            return 3
        log({"event": "baseline", "out": await gdc(mcp, BASELINE)})
        log({"event": "break_verify", "out": await gdc(mcp, BREAK_VERIFY, timeout=60)})
        for lo, hi in (("A", "M"), ("N", "Z")):
            code = CENSUS.replace("___LO___", lo).replace("___HI___", hi)
            log({"event": f"census_{lo}_{hi}", "out": await gdc(mcp, code)})
        log({"event": "done", "t": time.time()})
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
