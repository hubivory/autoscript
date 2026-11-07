from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm import ChainedLLM, LLMError, OutOfCredits  # noqa: E402
from llm_cli import clean_lines, extract_answer, failure_hint, strip_ansi  # noqa: E402


class Script:
    def __init__(self, script: list, provider: str = "x") -> None:
        self.script = script
        self.provider = provider
        self.calls = 0
        self.last_provider = ""

    async def chat(self, messages, model=None, max_tokens=8192):
        action = self.script[self.calls] if self.calls < len(self.script) else self.script[-1]
        self.calls += 1
        if isinstance(action, Exception):
            raise action
        self.last_provider = self.provider
        return action


def test_markers() -> None:
    pane = (
        "\x1b[20;1Hsome chrome\n"
        "user prompt echo here\n"
        "@@BEGIN@@\n"
        "```lua\nprint(1)\n```\n"
        "@@END@@\n"
        "\x1b[22;1H│ Enter a coding task or / for commands\n"
    )
    assert "print(1)" in extract_answer(pane)


def test_last_pair_wins() -> None:
    pane = (
        "start with a line containing only @@BEGIN@@ and ending @@END@@\n"
        "user prompt echo\n"
        "@@BEGIN@@\nPONG\n@@END@@\n"
        "Enter a coding task"
    )
    assert extract_answer(pane) == "PONG"


def test_chrome_filtered() -> None:
    text = "hello\n│ Enter a coding task or / for commands\nAd [Report 1]\nEnd session\nworld"
    lines = clean_lines(text)
    assert lines == ["hello", "world"], lines


def test_failure_hint() -> None:
    assert failure_hint("all good") is None
    hint = failure_hint("blah Rate limit reached blah")
    assert hint is not None and "Rate limit" in hint


def test_strip() -> None:
    assert strip_ansi("\x1b[20;1Hhi\x1b[0m") == "hi"


async def run_chain() -> None:
    chain = ChainedLLM(
        [
            Script([OutOfCredits("empty")], provider="first"),
            Script(["second-ok"], provider="second"),
        ]
    )
    out = await chain.chat([{"role": "user", "content": "hi"}])
    assert out == "second-ok", out
    assert chain.last_provider == "second", chain.last_provider

    chain = ChainedLLM([Script([LLMError("bad")])])
    try:
        await chain.chat([{"role": "user", "content": "hi"}])
    except LLMError:
        print("chain raises when all fail: ok")
        return
    raise AssertionError("expected LLMError")


def main() -> int:
    test_markers()
    test_last_pair_wins()
    print("markers: ok")
    test_chrome_filtered()
    print("chrome filter: ok")
    test_failure_hint()
    print("failure hint: ok")
    test_strip()
    print("strip: ok")
    asyncio.run(run_chain())
    print("chain order: ok")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
