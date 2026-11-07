from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import discord  # noqa: E402

import store  # noqa: E402
from config import Config  # noqa: E402
from discord_app import (  # noqa: E402
    MODEL_OPTIONS,
    ChannelMenuView,
    DetailModal,
    GameModal,
    MenuView,
    embed,
    failure_embed,
)
from pipeline import Result  # noqa: E402
import roblox  # noqa: E402


def test_embeds() -> None:
    thing = embed("🌸 Hi 🌸", "hello")
    assert thing.title == "🌸 Hi 🌸"
    assert thing.footer.text == "made with 💖"
    result = Result(
        game=roblox.GameRef(place_id=1, name="G"),
        script="print(1)",
        provider="x",
        verified=True,
        attempts=1,
        verification=["console clean"],
    )
    from discord_app import result_embed

    rendered = result_embed(result, "generate")
    assert "Load checked" in (rendered.title or "")
    failed = failure_embed("generate", ["bad"])
    assert "Failed" in (failed.title or "")
    print("embeds: ok")


def test_menu_view() -> None:
    from discord_app import ScriptBot

    bot = ScriptBot(Config(discord_token="x", freebuff_cli=True))
    view = MenuView(bot)
    kinds = sorted(type(item).__name__ for item in view.children)
    assert kinds == ["Button", "Button", "ModelSelect"], kinds
    selects = [i for i in view.children if isinstance(i, discord.ui.Select)]
    assert len(selects[0].options) == len(MODEL_OPTIONS) == 10
    assert len(MenuView(ScriptBot(Config(discord_token="x"))).children) == 2
    modal = GameModal(bot)
    assert len(modal.children) == 2
    detail = DetailModal(bot, "fix", "t", "p")
    assert len(detail.children) == 1
    print("menu view: ok")


def test_channel_view() -> None:
    from discord_app import ScriptBot

    bot = ScriptBot(Config(discord_token="x"))
    view = ChannelMenuView(bot)
    ids = sorted(item.custom_id for item in view.children)
    assert ids == [
        "scriptbot:fix",
        "scriptbot:info",
        "scriptbot:reverify",
        "scriptbot:rewrite",
        "scriptbot:update",
    ], ids
    print("channel view: ok")


def test_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        storage = store.Store(tmp)
        assert store.slugify("Break and Steal an Egg!", 123) == "break-and-steal-an-egg"
        assert store.slugify("", 0) == "game"
        assert store.slugify("!!!", 0) == "game"
        assert storage.load_session(9) is None
        session = store.new_session(1, 9, "G", 123, None, "Opus")
        storage.save_session(session)
        storage.save_script(9, 1, "print(1)")
        back = storage.load_session(9)
        assert back and back["game"] == "G"
        assert storage.get_script(9, 1) == "print(1)"
        storage.append_turn(9, "generate", "req", "print(2)", True, 1, "p", "m", ["ok"])
        back = storage.load_session(9)
        assert back["current_version"] == 1
        assert len(back["turns"]) == 1
        assert storage.get_script(9) == "print(2)"
        storage.log_history({"a": 1})
        assert os.path.isfile(os.path.join(tmp, "history.jsonl"))
    print("store: ok")


def main() -> int:
    test_embeds()
    test_menu_view()
    test_channel_view()
    test_store()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
