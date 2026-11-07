from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from aiohttp import web

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_client import MCPClient  # noqa: E402

TOOLS = {
    "list-clients": {
        "description": "list connected clients",
        "inputSchema": {"type": "object", "properties": {}},
        "reply": "aaaabbbb-cccc | Delta @ Test Game (place=114326934417838 job=test)",
    },
    "set-active-client": {
        "description": "select connected client",
        "inputSchema": {"type": "object", "properties": {"clientId": {"type": "string"}}},
        "reply": "ok",
    },
    "get-game-info": {
        "description": "game info",
        "inputSchema": {"type": "object", "properties": {}},
        "reply": "Break and Steal an Egg | services: ReplicatedStorage, Workspace",
    },
    "get-player-state": {
        "description": "player state",
        "inputSchema": {"type": "object", "properties": {}},
        "reply": "health=100 money=12345 position=(1,2,3)",
    },
    "find-game-systems": {
        "description": "game systems",
        "inputSchema": {"type": "object", "properties": {}},
        "reply": "ShopSystem remote=ReplicatedStorage.Remotes.BuyEgg",
    },
    "search-instances": {
        "description": "search instances",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "reply": "RemoteEvent: ReplicatedStorage.Remotes.BuyEgg",
    },
    "execute": {
        "description": "execute lua",
        "inputSchema": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
        "reply": "script executed",
    },
}


class MockBridge:
    def __init__(self) -> None:
        self.sessions: set[str] = set()
        self.web = web.Application()
        self.web.router.add_post("/mcp", self.handle)

    async def handle(self, request: web.Request) -> web.Response:
        payload = await request.json()
        sid = request.headers.get("Mcp-Session-Id")
        if sid is not None and sid not in self.sessions:
            return web.json_response({"error": "session gone"}, status=404)
        method = payload.get("method")
        msg_id = payload.get("id")
        headers: dict[str, str] = {}
        if method == "initialize":
            new_sid = uuid.uuid4().hex
            self.sessions.add(new_sid)
            headers["Mcp-Session-Id"] = new_sid
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mock-bridge", "version": "1.0"},
            }
            return web.json_response(
                {"jsonrpc": "2.0", "id": msg_id, "result": result}, headers=headers
            )
        if method and method.startswith("notifications/"):
            return web.Response(status=202)
        if method == "tools/list":
            tools = [
                {
                    "name": name,
                    "description": spec["description"],
                    "inputSchema": spec["inputSchema"],
                }
                for name, spec in TOOLS.items()
            ]
            return web.json_response(
                {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}
            )
        if method == "tools/call":
            params = payload.get("params") or {}
            name = params.get("name")
            spec = TOOLS.get(name)
            if not spec:
                return web.json_response(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32602, "message": f"unknown tool {name}"},
                    }
                )
            required = spec["inputSchema"].get("required") or []
            args = params.get("arguments") or {}
            missing = [r for r in required if r not in args]
            if missing:
                return web.json_response(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "isError": True,
                            "content": [{"type": "text", "text": f"missing {missing}"}],
                        },
                    }
                )
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": spec["reply"]}]
                    },
                }
            )
        return web.json_response(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"unknown method {method}"},
            }
        )


async def run() -> int:
    bridge = MockBridge()
    runner = web.AppRunner(bridge.web)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 16385)
    await site.start()
    failures = 0
    try:
        async with MCPClient("http://127.0.0.1:16385/mcp", timeout=15) as mcp:
            tools = await mcp.list_tools()
            print("tools:", tools)
            assert "get-game-info" in tools, "tool list missing"

            name = mcp.find_tool("get-game-info")
            assert name == "get-game-info"
            text = await mcp.call_tool(name, {})
            print("game-info:", text)
            assert "Break and Steal" in text

            search = mcp.find_tool("search-instances")
            key = mcp.arg_key(search, "query", "selector")
            assert key == "query", key
            text = await mcp.call_tool(search, {key: "RemoteEvent"})
            print("search:", text)
            assert "BuyEgg" in text

            ex = mcp.find_tool("execute")
            exkey = mcp.arg_key(ex, "code", "source")
            assert exkey == "code"
            print("execute:", await mcp.call_tool(ex, {exkey: "print(1)"}))

        import pipeline
        from config import Config

        cfg = Config(mcp_url="http://127.0.0.1:16385/mcp", request_timeout=15)
        pipe = pipeline.Pipeline(cfg)
        import roblox

        ref = roblox.GameRef(place_id=114326934417838, universe_id=1, name="Test Game")
        warnings: list[str] = []
        ctx, client = await pipe._gather(ref, "auto farm", warnings)
        print("context head:", ctx[:200].replace("\n", " | "))
        assert "### game-info" in ctx
        assert "BuyEgg" in ctx
        print("pipeline context ok; warnings:", warnings)
    except Exception as exc:
        failures += 1
        print("FAILED:", type(exc).__name__, exc)
    finally:
        await runner.cleanup()
    print("RESULT:", "PASS" if not failures else "FAIL")
    return failures


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
