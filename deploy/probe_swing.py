import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient

SETUP = """
local p = game:GetService("Players").LocalPlayer
local char = p.Character
if not char then return "no char" end
local target = Vector3.new(-350, 8, 0)
char:PivotTo(CFrame.new(target))
task.wait(1.5)
for _, t in ipairs(p.Backpack:GetChildren()) do
  if t:IsA("Tool") and t.Name == "Pickaxe" then
    char:FindFirstChildOfClass("Humanoid"):EquipTool(t)
    break
  end
end
task.wait(1)
local root = char:FindFirstChild("HumanoidRootPart")
local v = root and root.Position
return string.format("at %.0f,%.0f,%.0f tool=%s", v.X, v.Y, v.Z,
  tostring(char:FindFirstChildOfClass("Tool") and char:FindFirstChildOfClass("Tool").Name or "none"))
"""

SWING = """
local p = game:GetService("Players").LocalPlayer
local char = p.Character
local tool = char and char:FindFirstChildOfClass("Tool")
if tool then
  tool:Activate()
  return "swung " .. tool.Name
end
return "no tool"
"""


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        print("setup:", (await mcp.call_tool("execute", {"code": SETUP}))[:200])

        async def spy() -> str:
            try:
                return await mcp.call_tool("remote-spy", {"duration": 20})
            except Exception as exc:
                return f"SPY FAILED: {exc}"

        async def swing() -> str:
            await asyncio.sleep(4)
            try:
                return await mcp.call_tool("execute", {"code": SWING})
            except Exception as exc:
                return f"SWING FAILED: {exc}"

        spy_out, swing_out = await asyncio.gather(spy(), swing())
        print("swing:", (swing_out or "")[:200])
        print("=== SPY (egg/hit/swing lines) ===")
        for line in (spy_out or "").splitlines():
            low = line.lower()
            if any(k in low for k in ("egghit", "bathit", "swing", "pickaxe")):
                print(line[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
