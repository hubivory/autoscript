from __future__ import annotations

import asyncio
import itertools
import json
from typing import Any

import aiohttp


class MCPError(RuntimeError):
    pass


class MCPClient:
    """Minimal MCP Streamable HTTP client for the mcp-mobile bridge."""

    def __init__(
        self,
        url: str,
        token: str = "",
        timeout: int = 180,
        protocol_version: str = "2025-06-18",
    ) -> None:
        self.url = url
        self.token = token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.protocol_version = protocol_version
        self.session_id: str | None = None
        self._ids = itertools.count(1)
        self._http: aiohttp.ClientSession | None = None
        self._init_lock = asyncio.Lock()
        self._initialized = False
        self.server_info: dict[str, Any] = {}
        self.tools: list[str] = []
        self.tool_defs: dict[str, dict[str, Any]] = {}

    async def __aenter__(self) -> "MCPClient":
        self._http = aiohttp.ClientSession(timeout=self.timeout)
        try:
            await self.initialize()
        except BaseException:
            await self._http.close()
            self._http = None
            self._initialized = False
            raise
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._http is not None:
            await self._http.close()
            self._http = None
        self._initialized = False

    def _headers(self) -> dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.protocol_version,
        }
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def _http_session(self) -> aiohttp.ClientSession:
        if self._http is None:
            self._http = aiohttp.ClientSession(timeout=self.timeout)
        return self._http

    @staticmethod
    def _parse_sse(body: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        data_lines: list[str] = []
        for line in body.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif line == "" and data_lines:
                payload = "\n".join(data_lines).strip()
                data_lines = []
                if payload and payload != "[DONE]":
                    try:
                        messages.append(json.loads(payload))
                    except json.JSONDecodeError:
                        pass
        if data_lines:
            payload = "\n".join(data_lines).strip()
            if payload:
                try:
                    messages.append(json.loads(payload))
                except json.JSONDecodeError:
                    pass
        return messages

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        http = await self._http_session()
        async with http.post(self.url, json=payload, headers=self._headers()) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self.session_id = sid
            if resp.status == 202:
                return None
            if resp.status in (400, 404, 410):
                text = await resp.text()
                raise _SessionGone(f"{resp.status}: {text[:200]}")
            if resp.status >= 400:
                text = await resp.text()
                raise MCPError(f"HTTP {resp.status}: {text[:500]}")
            ctype = resp.headers.get("Content-Type", "")
            body = await resp.text()
            if "text/event-stream" in ctype:
                messages = self._parse_sse(body)
                for msg in messages:
                    if msg.get("id") == payload.get("id"):
                        return msg
                return None
            if not body.strip():
                return None
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                messages = self._parse_sse(body)
                return messages[-1] if messages else None

    async def _request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": next(self._ids),
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        try:
            msg = await self._post(payload)
        except _SessionGone:
            self._initialized = False
            self.session_id = None
            if method != "initialize":
                await self.initialize()
            payload["id"] = next(self._ids)
            msg = await self._post(payload)
        if msg is None:
            raise MCPError(f"empty response for {method}")
        if "error" in msg:
            err = msg["error"]
            raise MCPError(f"{method}: {err.get('message', err)}")
        return msg.get("result")

    async def _notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        try:
            await self._post(payload)
        except _SessionGone:
            pass

    async def initialize(self) -> None:
        async with self._init_lock:
            if self._initialized:
                return
            result = await self._request(
                "initialize",
                {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {},
                    "clientInfo": {"name": "scriptbot", "version": "1.0.0"},
                },
            )
            self.server_info = result or {}
            await self._notify("notifications/initialized")
            self._initialized = True

    async def list_tools(self) -> list[str]:
        result = await self._request("tools/list", {})
        tools = (result or {}).get("tools", [])
        self.tool_defs = {
            str(t.get("name")): t for t in tools if isinstance(t, dict) and t.get("name")
        }
        self.tools = list(self.tool_defs)
        return self.tools

    def find_tool(self, *candidates: str) -> str | None:
        normalized = {
            name.replace("_", "-").lower(): name for name in self.tool_defs
        }
        for cand in candidates:
            key = cand.replace("_", "-").lower()
            if key in normalized:
                return normalized[key]
        for cand in candidates:
            key = cand.replace("_", "-").lower()
            for norm, name in normalized.items():
                if key in norm:
                    return name
        return None

    def arg_key(self, tool: str, *candidates: str) -> str | None:
        schema = self.tool_defs.get(tool, {}).get("inputSchema") or {}
        props = schema.get("properties") or {}
        if not props:
            return candidates[0] if candidates else None
        for cand in candidates:
            if cand in props:
                return cand
        required = schema.get("required") or []
        if required:
            return required[0]
        return next(iter(props), None)

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        result = await self._request(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        if not result:
            return ""
        if result.get("isError"):
            return f"ERROR: {_content_text(result)}"
        return _content_text(result)


class _SessionGone(Exception):
    pass


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif item.get("type") == "resource":
                    parts.append(str(item.get("resource", {}).get("text", "")))
        return "\n".join(p for p in parts if p)
    if isinstance(content, str):
        return content
    return json.dumps(result, ensure_ascii=False)[:20000]
