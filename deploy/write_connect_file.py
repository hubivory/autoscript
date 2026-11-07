import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from pipeline import Pipeline


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/delta_connect.txt"
    config = Config.from_env()
    script = await Pipeline(config).connector_script("")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(script + "\n")
    print(f"wrote {out} ({len(script)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
