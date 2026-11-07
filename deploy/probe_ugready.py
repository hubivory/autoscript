import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from pipeline import Pipeline


class _LLM:
    last_provider = "test"


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    pipe = Pipeline(config, llm=_LLM())
    print("BASE:", pipe._public_base())
    print("--- STATUS ---")
    print(await pipe.status())
    print("--- CONNECT (first line) ---")
    print((await pipe.connector_script("")).splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
