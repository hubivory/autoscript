from __future__ import annotations

import datetime
import json
import os
import re
from typing import Any


def utcnow() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def slugify(name: str, place_id: int = 0) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:90].strip("-")
    if not slug:
        slug = f"game-{place_id}" if place_id else "game"
    return slug


def channel_slug(name: str, place_id: int) -> str:
    suffix = f"-{place_id}"
    return slugify(name, place_id)[:100 - len(suffix)].rstrip("-") + suffix


def new_session(
    guild_id: int,
    channel_id: int,
    game: str,
    place_id: int,
    universe_id: int | None = None,
    model_filter: str = "",
) -> dict[str, Any]:
    now = utcnow()
    return {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "channel_name": "",
        "game": game,
        "place_id": place_id,
        "universe_id": universe_id,
        "model_filter": model_filter,
        "model_actual": "",
        "provider": "",
        "created_at": now,
        "updated_at": now,
        "menu_message_id": None,
        "current_version": 0,
        "turns": [],
    }


class Store:
    def __init__(self, root: str) -> None:
        self.root = root
        self.sessions_dir = os.path.join(root, "sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _session_path(self, channel_id: int) -> str:
        return os.path.join(self.sessions_dir, f"{channel_id}.json")

    def _script_path(self, channel_id: int, version: int) -> str:
        folder = os.path.join(self.sessions_dir, str(channel_id))
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"v{version}.lua")

    def save_session(self, session: dict[str, Any]) -> None:
        session["updated_at"] = utcnow()
        path = self._session_path(int(session["channel_id"]))
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(session, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def load_session(self, channel_id: int) -> dict[str, Any] | None:
        path = self._session_path(channel_id)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def save_script(self, channel_id: int, version: int, script: str) -> str:
        path = self._script_path(channel_id, version)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(script)
        return path

    def get_script(self, channel_id: int, version: int | None = None) -> str | None:
        session = self.load_session(channel_id)
        if not session:
            return None
        if version is None:
            version = int(session.get("current_version", 0))
        if version <= 0:
            return None
        path = self._script_path(channel_id, version)
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def append_turn(
        self,
        channel_id: int,
        kind: str,
        request: str,
        script: str,
        verified: bool,
        attempts: int,
        provider: str,
        model_actual: str,
        verification: list[str],
    ) -> dict[str, Any]:
        session = self.load_session(channel_id)
        if not session:
            raise KeyError(f"no session for channel {channel_id}")
        version = int(session.get("current_version", 0)) + 1
        session["current_version"] = version
        session["provider"] = provider
        if model_actual:
            session["model_actual"] = model_actual
        session.setdefault("turns", []).append(
            {
                "n": version,
                "ts": utcnow(),
                "kind": kind,
                "request": request[:2000],
                "verified": verified,
                "attempts": attempts,
                "verification": list(verification or [])[:40],
            }
        )
        self.save_script(channel_id, version, script)
        self.save_session(session)
        return session

    def log_history(self, entry: dict[str, Any]) -> None:
        entry = dict(entry)
        entry.setdefault("ts", utcnow())
        path = os.path.join(self.root, "history.jsonl")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
