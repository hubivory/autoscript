import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_cli import FreebuffCLIClient


async def main() -> int:
    client = FreebuffCLIClient(timeout=420)
    out = await client.chat(
        [
            {
                "role": "user",
                "content": "Reply with exactly PONG-CLIPROBE and nothing else. "
                "Do not run commands.",
            }
        ]
    )
    print("ANSWER:", out[:500])
    print("provider:", client.last_provider)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
