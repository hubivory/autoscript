import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from pipeline import Pipeline


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    host = sys.argv[1] if len(sys.argv) > 1 else ""
    config = Config.from_env()
    pipe = Pipeline(config)
    print("== status ==")
    print(await pipe.status())
    print("== loadstring ==")
    try:
        text = await pipe.connector_script(host)
        if pipe.config.mcp_token:
            text = text.replace(pipe.config.mcp_token, "<redacted>")
        print(text)
    except Exception as exc:
        print("loadstring failed:", exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
