from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from aiohttp import web

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import roblox  # noqa: E402
from config import Config  # noqa: E402
from mcp_client import MCPClient  # noqa: E402
from pipeline import Pipeline, VerificationFailed  # noqa: E402


class FakeLLM:
    def __init__(self, scripts: list[str]) -> None:
        self.scripts = scripts
        self.calls = 0
        self.last_provider = "fake"
        self.last_model_actual = ""

    async def chat(self, messages, model=None, max_tokens=8192):
        text = self.scripts[min(self.calls, len(self.scripts) - 1)]
        self.calls += 1
        return text


STATE = {"console": ["[Log] boot ok", "[Log] welcome"], "guis": 0}

SCRIPT = '''--// Snowy - Test Game
local url = "https://raw.githubusercontent.com/0x1s2s/Snowy-Ui-Library/refs/heads/main/SnowyUi"
local Library = loadstring(game:HttpGet(url))()
local window = Library:Window({ Title = "Snowy Studios", Subtitle = "Test Game" })
window:Tab({ Name = "UI Settings" })
getgenv().SnowyStudiosUnload = function() Library:Unload() end
print("Snowy Test Game loaded")
'''


def schema(props: dict, required: list | None = None) -> dict:
    out: dict = {"type": "object", "properties": props}
    if required:
        out["required"] = required
    return out


TOOLS = {
    "list-clients": ({}, "aaaabbbb-cccc | T @ Old Game (place=111 job=j)\nccccdddd-eeee | T @ Test Game (place=114326934417838 job=k)"),
    "set-active-client": ({"clientId": {"type": "string"}}, "ok"),
    "get-ai-script-context": ({"goal": {"type": "string"}}, "brief: shop + remotes"),
    "get-game-info": ({}, "Game Test Game"),
    "get-player-state": ({}, "health 100"),
    "search-instances": ({"selector": {"type": "string"}}, "RemoteEvent X"),
    "get-console-output": ({"limit": {"type": "number"}}, None),
    "execute-file": ({"content": {"type": "string"}}, None),
    "get-data-by-code": ({"code": {"type": "string"}}, None),
}


class MockBridge:
    def __init__(self) -> None:
        self.sessions: set[str] = set()
        self.web = web.Application()
        self.web.router.add_post("/mcp", self.handle)

    async def handle(self, request: web.Request) -> web.Response:
        import uuid

        payload = await request.json()
        sid = request.headers.get("Mcp-Session-Id")
        if sid is not None and sid not in self.sessions:
            return web.json_response({"error": "gone"}, status=404)
        method = payload.get("method")
        msg_id = payload.get("id")
        headers: dict[str, str] = {}
        if method == "initialize":
            new_sid = uuid.uuid4().hex
            self.sessions.add(new_sid)
            headers["Mcp-Session-Id"] = new_sid
            return web.json_response(
                {"jsonrpc": "2.0", "id": msg_id, "result": {
                    "protocolVersion": "2025-06-18", "capabilities": {},
                    "serverInfo": {"name": "mock", "version": "1"}}},
                headers=headers,
            )
        if method and method.startswith("notifications/"):
            return web.Response(status=202)
        if method == "tools/list":
            tools = [
                {"name": n, "description": n, "inputSchema": schema(*self._sr(n))}
                for n in TOOLS
            ]
            return web.json_response(
                {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}
            )
        if method == "tools/call":
            params = payload.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            text = self._call(name, args)
            return web.json_response(
                {"jsonrpc": "2.0", "id": msg_id,
                 "result": {"content": [{"type": "text", "text": text}]}})
        return web.json_response(
            {"jsonrpc": "2.0", "id": msg_id,
             "error": {"code": -32601, "message": "nope"}})

    def _sr(self, name: str):
        props, _ = TOOLS[name]
        required = None
        if name in ("set-active-client", "execute-file", "get-data-by-code"):
            required = list(props.keys())
        return props, required

    def _call(self, name: str, args: dict) -> str:
        if name == "get-console-output":
            return "\n".join(STATE["console"])
        if name == "execute-file":
            content = args.get("content", "")
            if "BROKEN" in content:
                STATE["console"].append("Players.T.PlayerScripts:12: attempt to index nil with 'X'")
                STATE["console"].append("Stack Begin")
                STATE["console"].append("Stack End")
            else:
                STATE["console"].append("Test Game loaded")
            return "ok"
        if name == "get-data-by-code":
            code = args.get("code", "")
            if "gethui" in code:
                STATE["guis"] += 1
                if STATE["guis"] >= 2:
                    return "Topbar,MainGUI,SnowyHub"
                return "Topbar,MainGUI"
            if "PlaceId" in code:
                return "114326934417838"
            return "nil"
        return TOOLS[name][1]


async def fake_resolve(session, text: str):
    return roblox.GameRef(place_id=114326934417838, universe_id=1, name="Test Game")


async def scenario_fix_then_pass() -> None:
    roblox.resolve = fake_resolve  # type: ignore[method-assign]
    cfg = Config(mcp_url="http://127.0.0.1:16387/mcp", request_timeout=20)
    llm = FakeLLM([
        "```lua\n-- BROKEN\n" + SCRIPT + "\n```",
        "```lua\n" + SCRIPT + "\n```",
    ])
    pipe = Pipeline(cfg, llm=llm)
    result = await pipe.generate("Test Game", "auto farm", verify=True, max_attempts=3)
    assert result.verified, result.verification
    assert result.attempts == 2, result.attempts
    assert "BROKEN" not in result.script
    assert llm.calls == 2, llm.calls
    print("fix-then-pass: ok", result.verification)


async def scenario_always_broken() -> None:
    STATE["console"] = ["[Log] boot ok"]
    STATE["guis"] = 0
    roblox.resolve = fake_resolve  # type: ignore[method-assign]
    cfg = Config(mcp_url="http://127.0.0.1:16387/mcp", request_timeout=20)
    llm = FakeLLM(["```lua\n-- BROKEN\n" + SCRIPT + "\n```"])
    pipe = Pipeline(cfg, llm=llm)
    try:
        await pipe.generate("Test Game", "x", verify=True, max_attempts=2)
    except VerificationFailed as exc:
        assert len(exc.log) > 0
        assert llm.calls == 2, llm.calls
        print("always-broken raises: ok")
        return
    raise AssertionError("expected VerificationFailed")


async def scenario_on_stage() -> None:
    roblox.resolve = fake_resolve  # type: ignore[method-assign]
    cfg = Config(mcp_url="http://127.0.0.1:16387/mcp", request_timeout=20)
    llm = FakeLLM(["```lua\n" + SCRIPT + "\n```"])
    pipe = Pipeline(cfg, llm=llm)
    stages: list[str] = []

    async def _collect(message: str) -> None:
        stages.append(message)

    result = await pipe.generate("Test Game", "auto farm", verify=True, max_attempts=1, on_stage=_collect)
    assert result.verified, result.verification
    joined = " ".join(stages)
    for marker in ("Resolving", "Gathering", "Generating", "verifying"):
        assert marker in joined, (marker, stages)
    print("on-stage emits: ok", len(stages))


async def main() -> int:
    bridge = MockBridge()
    runner = web.AppRunner(bridge.web)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 16387)
    await site.start()
    failures = 0
    try:
        async with MCPClient("http://127.0.0.1:16387/mcp", timeout=15) as mcp:
            assert "execute-file" in await mcp.list_tools()
        await scenario_fix_then_pass()
        await scenario_always_broken()
        await scenario_on_stage()
    except Exception as exc:
        failures += 1
        print("FAILED:", type(exc).__name__, exc)
    finally:
        await runner.cleanup()
    print("RESULT:", "PASS" if not failures else "FAIL")
    return failures


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
