import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from mcp_client import MCPClient


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    async with MCPClient(config.mcp_url, config.mcp_token, timeout=120) as mcp:
        await mcp.list_tools()
        checks = {
            "pos": "local r=game.Players.LocalPlayer.Character:FindFirstChild('HumanoidRootPart') local v=r and r.Position return v and string.format('%.0f,%.0f,%.0f',v.X,v.Y,v.Z) or 'nochar'",
            "tool": "local t=game.Players.LocalPlayer.Character:FindFirstChildOfClass('Tool') return t and t.Name or 'none'",
            "nearby": "local out={} local pp=game.Players.LocalPlayer.Character:FindFirstChild('HumanoidRootPart').Position for _,d in ipairs(Workspace:GetDescendants()) do if #out>=5 then break end if d:IsA('Model') and string.find(d.Name,'Nest',1,true) then local ok,pv=pcall(function() return d:GetPivot().Position end) if ok then local dist=(pv-pp).Magnitude if dist<120 then out[#out+1]=d.Name..'@'..math.floor(dist) end end end end return table.concat(out,',')",
        }
        for label, code in checks.items():
            try:
                out = await mcp.call_tool("get-data-by-code", {"code": code})
            except Exception as exc:
                out = f"FAILED: {exc}"
            print(f"{label}: {(out or '')[:600]}")
        print("=== spy sample (5s) ===")
        try:
            out = await mcp.call_tool("remote-spy", {"duration": 5})
        except Exception as exc:
            out = f"FAILED: {exc}"
        print((out or "")[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
