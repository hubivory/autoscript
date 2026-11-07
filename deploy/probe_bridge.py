import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import MCPClient


async def main() -> int:
    token_path = os.path.expanduser("~/.mcp_bridge_token")
    token = open(token_path).read().strip() if os.path.exists(token_path) else ""
    url = os.getenv("MCP_URL", "http://127.0.0.1:16384/mcp")
    async with MCPClient(url, token, timeout=30) as mcp:
        tools = await mcp.list_tools()
        print("tool count:", len(tools))
        print("tools:", ", ".join(tools))
        name = mcp.find_tool("list-clients", "clients")
        if name:
            print("list-clients:", (await mcp.call_tool(name, {}))[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
