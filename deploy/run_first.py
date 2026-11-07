import asyncio
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, load_env
from pipeline import Pipeline, VerificationFailed


async def main() -> int:
    load_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    config = Config.from_env()
    pipe = Pipeline(config)
    start = time.time()
    out: dict = {"started": start}
    try:
        result = await pipe.generate(
            "114326934417838", "auto farm eggs", verify=True, max_attempts=3
        )
        with open("/tmp/first_script.lua", "w", encoding="utf-8") as handle:
            handle.write(result.script)
        out.update(
            ok=True,
            verified=result.verified,
            attempts=result.attempts,
            provider=result.provider,
            model=result.model_actual,
            warnings=result.warnings,
            verification=result.verification,
            script_chars=len(result.script),
            elapsed=round(time.time() - start, 1),
        )
    except VerificationFailed as exc:
        out.update(ok=False, verified=False, log=exc.log, elapsed=round(time.time() - start, 1))
    except Exception as exc:  # noqa: BLE001
        out.update(
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
            traceback=traceback.format_exc()[-3000:],
            elapsed=round(time.time() - start, 1),
        )
    with open("/tmp/first_run.json", "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != "traceback"}, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
