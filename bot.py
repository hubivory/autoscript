from __future__ import annotations

import logging
import os
import sys

from config import Config, load_env

LOG = logging.getLogger("scriptbot")


def _check(config: Config, problems: list[str]) -> int:
    for problem in problems:
        print(f"config: {problem}")
    for module in ("mcp_client", "roblox", "llm", "pipeline"):
        try:
            __import__(module)
            print(f"import {module}: ok")
        except Exception as exc:
            print(f"import {module}: FAILED {exc}")
            return 1
    try:
        import discord

        if not hasattr(discord, "app_commands"):
            print("discord.py: installed package lacks app_commands (need real discord.py>=2.4)")
            return 1
        import discord_app

        discord_app  # noqa: F841
        print("import discord_app: ok")
    except Exception as exc:
        print(f"import discord_app: FAILED {exc}")
        return 1
    if problems:
        return 1
    print("config: ok")
    return 0


def main(argv: list[str]) -> int:
    load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    config = Config.from_env()
    problems = config.validate()
    if "--check" in argv:
        return _check(config, problems)
    fatal = [p for p in problems if "DISCORD_TOKEN" in p]
    if fatal:
        for p in fatal:
            print(f"config: {p}")
        return 1
    for p in problems:
        print(f"config warning: {p}")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    from discord_app import build_bot

    bot = build_bot(config)
    bot.run(config.discord_token, log_handler=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
