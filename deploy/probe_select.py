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
                "content": "Reply with exactly PONG-MODEL and nothing else. "
                "Do not run commands.",
            }
        ],
        model="Opus",
    )
    print("ACTUAL MODEL:", client.last_model_actual)
    print("ANSWER:", out[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
