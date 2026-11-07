from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from aiohttp import web

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm import LLMClient, OutOfCredits, extract_lua  # noqa: E402

SCRIPT = "```lua\nprint('hi')\n```"


def make_app(behaviour: dict[str, str]) -> web.Application:
    app = web.Application()

    async def handler(request: web.Request) -> web.Response:
        mode = request.match_info.get("mode") or "primary"
        behaviour_mode = behaviour.get(mode, "ok")
        if behaviour_mode == "credits":
            return web.json_response(
                {"error": {"message": "insufficient credits"}}, status=429
            )
        if behaviour_mode == "key":
            return web.json_response({"error": "bad key"}, status=401)
        return web.json_response(
            {
                "choices": [
                    {"message": {"role": "assistant", "content": SCRIPT}}
                ]
            }
        )

    app.router.add_post("/{mode}/chat/completions", handler)

    async def models(request: web.Request) -> web.Response:
        mode = request.match_info.get("mode")
        if behaviour.get(mode) == "auth-fail":
            return web.json_response({"error": "bad key"}, status=401)
        return web.json_response(
            {"data": [{"id": "deepseek-v4-pro", "name": "DeepSeek V4.1 Pro"}]}
        )

    app.router.add_get("/{mode}/models", models)
    return app


async def main() -> int:
    failures = 0
    behaviour = {"primary": "ok", "fallback": "ok"}
    app = make_app(behaviour)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 16386)
    await site.start()
    base = "http://127.0.0.1:16386"
    msgs = [{"role": "user", "content": "write a script"}]
    try:
        client = LLMClient(
            api_key="k",
            model="m",
            url=f"{base}/primary/chat/completions",
            fallback_key="fk",
            fallback_model="fm",
            fallback_url=f"{base}/fallback/chat/completions",
            timeout=15,
        )
        text = await client.chat(msgs)
        print("primary ok:", client.last_provider, repr(text[:30]))
        assert client.last_provider == "primary"
        assert extract_lua(text) == "print('hi')"

        behaviour["primary"] = "credits"
        text = await client.chat(msgs)
        print("credits fallback:", client.last_provider)
        assert client.last_provider == "fallback", client.last_provider

        behaviour["primary"] = "ok"
        no_fallback = LLMClient(
            api_key="k",
            model="m",
            url=f"{base}/primary/chat/completions",
            timeout=15,
        )
        behaviour["primary"] = "credits"
        try:
            await no_fallback.chat(msgs)
            raise AssertionError("expected OutOfCredits")
        except OutOfCredits:
            print("no-fallback raises OutOfCredits: ok")

        behaviour["primary"] = "ok"
        model_client = LLMClient(
            api_key="k",
            model="m",
            url=f"{base}/primary/chat/completions",
            timeout=15,
        )
        models = await model_client.list_models()
        assert models and models[0]["id"] == "deepseek-v4-pro", models
        print("list_models: ok")

        behaviour["primary"] = "auth-fail"
        try:
            await model_client.list_models()
            raise AssertionError("expected OutOfCredits on 401")
        except OutOfCredits:
            print("list_models 401: ok")

        from llm import LLMError

        sess = LLMClient(
            api_key="123e4567-e89b-12d3-a456-426614174000",
            model="m",
            url="https://freebuff.com/api/v1/paid/chat/completions",
            timeout=15,
        )
        try:
            await sess.chat(msgs)
            raise AssertionError("expected LLMError for session token")
        except LLMError as exc:
            assert "session token" in str(exc).lower()
            print("session-token guard: ok")
    except Exception as exc:
        failures += 1
        print("FAILED:", type(exc).__name__, exc)
    finally:
        await runner.cleanup()
    print("RESULT:", "PASS" if not failures else "FAIL")
    return failures


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
