import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import MCPClient

WANTED = [
    "get-ai-script-context",
    "execute",
    "execute-file",
    "get-game-info",
    "get-player-state",
    "get-game-guis",
    "find-game-systems",
    "search-instances",
    "script-grep",
    "get-script-content",
    "get-loadstring",
    "get-connector-health",
    "remote-spy",
    "get-data-by-code",
    "get-console-output",
    "set-active-client",
    "click-button",
    "type-text-box",
    "get-descendants-tree",
    "list-roblox-windows",
    "semantic-search-scripts",
]


async def main() -> int:
    token_path = os.path.expanduser("~/.mcp_bridge_token")
    token = open(token_path).read().strip() if os.path.exists(token_path) else ""
    url = os.getenv("MCP_URL", "http://127.0.0.1:16384/mcp")
    async with MCPClient(url, token, timeout=30) as mcp:
        await mcp.list_tools()
        for name in WANTED:
            definition = mcp.tool_defs.get(name)
            if not definition:
                print(f"== {name}: MISSING")
                continue
            desc = (definition.get("description") or "").strip().splitlines()
            print(f"== {name}")
            print("   desc:", desc[0][:140] if desc else "")
            print("   schema:", json.dumps(definition.get("inputSchema") or {}, ensure_ascii=False)[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
