from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import aiohttp

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) scriptbot/1.0"


@dataclass
class GameRef:
    place_id: int
    universe_id: int | None = None
    name: str = ""
    creator: str = ""
    playing: int | None = None

    def label(self) -> str:
        bits = [self.name or f"place {self.place_id}"]
        if self.creator:
            bits.append(f"by {self.creator}")
        return " ".join(bits)


class RobloxError(RuntimeError):
    pass


def parse_place_id(text: str) -> int | None:
    text = text.strip()
    if text.isdigit():
        return int(text)
    for pattern in (
        r"roblox\.com/games/(\d+)",
        r"[?&]placeId=(\d+)",
        r"roblox\.com/(?:experiences|games)/start\?.*?placeId=(\d+)",
        r"/(\d{6,})",
    ):
        m = re.search(pattern, text)
        if m:
            return int(m.group(1))
    return None


async def _get_json(
    session: aiohttp.ClientSession, url: str, timeout: int = 25, **kwargs: Any
) -> Any:
    try:
        async with session.get(
            url,
            headers={"User-Agent": UA},
            timeout=aiohttp.ClientTimeout(total=timeout),
            **kwargs,
        ) as resp:
            if resp.status != 200:
                return None
            try:
                return await resp.json(content_type=None)
            except Exception:
                return None
    except (asyncio.TimeoutError, aiohttp.ClientError, OSError):
        return None


def _walk_places(node: Any, out: list[dict[str, Any]], depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(node, dict):
        if "placeId" in node and isinstance(node.get("placeId"), int):
            out.append(node)
        for value in node.values():
            _walk_places(value, out, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _walk_places(value, out, depth + 1)


def _rank_game(game: dict[str, Any], query: str) -> tuple[int, int]:
    """Favor the requested title before popularity in ambiguous searches."""
    clean = lambda value: re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()
    title = clean(game.get("name") or game.get("displayName") or "")
    wanted = clean(query)
    match = 3 if title == wanted else 2 if title.startswith(wanted) else 1 if wanted in title else 0
    try:
        playing = int(game.get("playerCount") or game.get("playing") or 0)
    except (TypeError, ValueError):
        playing = 0
    return match, playing


async def search_place(session: aiohttp.ClientSession, query: str) -> GameRef | None:
    q = query.strip()
    if not q:
        return None
    url = (
        "https://apis.roblox.com/search-api/omni-search"
        f"?searchQuery={quote(q, safe='')}"
        "&sessionId=scriptbot&pageType=all"
    )
    data = await _get_json(session, url)
    if data:
        found: list[dict[str, Any]] = []
        _walk_places(data, found)
        scored = [
            f for f in found
            if isinstance(f.get("placeId"), int) and f.get("placeId", 0) > 0
        ]
        scored.sort(key=lambda f: _rank_game(f, q), reverse=True)
        if scored:
            best = scored[0]
            universe = best.get("universeId")
            return GameRef(
                place_id=int(best["placeId"]),
                universe_id=int(universe) if isinstance(universe, int) else None,
                name=str(best.get("name") or best.get("displayName") or ""),
                creator=_creator_name(best),
                playing=best.get("playerCount") or best.get("playing"),
            )
    legacy = (
        "https://games.roblox.com/v1/games/list"
        f"?model.keyword={quote(q, safe='')}&model.maxRows=10"
    )
    data = await _get_json(session, legacy)
    games = (data or {}).get("games") if isinstance(data, dict) else None
    if games:
        best = max(games, key=lambda g: _rank_game(g, q))
        return GameRef(
            place_id=int(best.get("placeId") or 0),
            universe_id=int(best.get("universeId") or 0) or None,
            name=str(best.get("name") or ""),
            creator=str(best.get("creatorName") or ""),
            playing=best.get("playerCount"),
        )
    return None


def _creator_name(node: dict[str, Any]) -> str:
    creator = node.get("creator")
    if isinstance(creator, dict):
        return str(creator.get("name") or "")
    return str(node.get("creatorName") or "")


async def resolve(session: aiohttp.ClientSession, text: str) -> GameRef:
    place_id = parse_place_id(text)
    if place_id is None:
        ref = await search_place(session, text)
        if ref is None:
            raise RobloxError(f"could not resolve '{text}' to a Roblox place")
        return await enrich(session, ref)
    return await enrich(session, GameRef(place_id=place_id))


async def enrich(session: aiohttp.ClientSession, ref: GameRef) -> GameRef:
    if ref.universe_id is None:
        data = await _get_json(
            session, f"https://apis.roblox.com/universes/v1/places/{ref.place_id}/universe"
        )
        if isinstance(data, dict) and isinstance(data.get("universeId"), int):
            ref.universe_id = data["universeId"]
    if ref.universe_id:
        data = await _get_json(
            session,
            f"https://games.roblox.com/v1/games?universeIds={ref.universe_id}",
        )
        rows = (data or {}).get("data") if isinstance(data, dict) else None
        if rows:
            row = rows[0]
            ref.name = ref.name or str(row.get("name") or "")
            ref.creator = ref.creator or str(row.get("creator", {}).get("name") or "")
            ref.playing = ref.playing or row.get("playing")
    return ref
