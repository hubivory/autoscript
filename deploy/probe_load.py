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
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/attempt2_script.lua"
    with open(path, encoding="utf-8") as handle:
        script = handle.read()
    print("script chars:", len(script))
    ref = roblox.GameRef(
        place_id=114326934417838,
        universe_id=10765288803,
        name="Break and Steal an Egg",
    )
    warnings: list[str] = []
    ok, log = await pipe._verify(script, ref, warnings)
    print("VERIFIED:", ok)
    for line in log:
        print(" -", line)
    print("warnings:", warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
