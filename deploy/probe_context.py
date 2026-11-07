import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import roblox
from config import Config, load_env
from pipeline import Pipeline


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    pipe = Pipeline(config)
    ref = roblox.GameRef(place_id=114326934417838)
    warnings: list[str] = []
    context, client = await pipe._gather(ref, "auto farm eggs test", warnings)
    print("client:", client)
    print("warnings:", warnings)
    print("context chars:", len(context))
    print("==== CONTEXT ====")
    print(context[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
