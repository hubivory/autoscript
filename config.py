from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def load_env(path: str | Path = ".env") -> None:
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass(frozen=True)
class Config:
    discord_token: str = ""
    command_prefix: str = "!"
    guild_ids: list[int] = field(default_factory=list)

    mcp_url: str = "http://127.0.0.1:16384/mcp"
    mcp_token: str = ""
    connect_host: str = ""

    perplexity_key: str = ""
    perplexity_model: str = "sonar-pro"
    perplexity_url: str = "https://api.perplexity.ai/chat/completions"

    freebuff_key: str = ""
    freebuff_model: str = "deepseek-v4-pro"
    freebuff_url: str = "https://freebuff.com/api/v1/paid/chat/completions"

    freebuff_cli: bool = False
    freebuff_bin: str = "/home/ubuntu/.nvm/versions/node/v20.20.2/bin/freebuff"
    freebuff_cli_model: str = ""
    freebuff_cli_timeout: int = 600

    gemini_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

    fallback_key: str = ""
    fallback_model: str = ""
    fallback_url: str = ""

    max_context_chars: int = 60000
    request_timeout: int = 180
    data_dir: str = "data"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            discord_token=os.getenv("DISCORD_TOKEN", ""),
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            guild_ids=[int(x) for x in _csv("GUILD_IDS") if x.isdigit()],
            mcp_url=os.getenv("MCP_URL", "http://127.0.0.1:16384/mcp"),
            mcp_token=os.getenv("MCP_AUTH_TOKEN") or os.getenv("PHONE_BRIDGE_TOKEN", ""),
            connect_host=os.getenv("CONNECT_HOST", ""),
            perplexity_key=os.getenv("PERPLEXITY_API_KEY", ""),
            perplexity_model=os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
            perplexity_url=os.getenv(
                "PERPLEXITY_URL", "https://api.perplexity.ai/chat/completions"
            ),
            freebuff_key=os.getenv("FREEBUFF_API_KEY", ""),
            freebuff_model=os.getenv("FREEBUFF_MODEL", "deepseek-v4-pro"),
            freebuff_url=os.getenv(
                "FREEBUFF_URL", "https://freebuff.com/api/v1/paid/chat/completions"
            ),
            freebuff_cli=os.getenv("FREEBUFF_CLI", "").strip().lower()
            in ("1", "true", "yes", "on"),
            freebuff_bin=os.getenv(
                "FREEBUFF_BIN",
                "/home/ubuntu/.nvm/versions/node/v20.20.2/bin/freebuff",
            ),
            freebuff_cli_model=os.getenv("FREEBUFF_CLI_MODEL", ""),
            freebuff_cli_timeout=int(os.getenv("FREEBUFF_CLI_TIMEOUT", "600")),
            gemini_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            gemini_url=os.getenv(
                "GEMINI_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            ),
            fallback_key=os.getenv("FALLBACK_API_KEY", ""),
            fallback_model=os.getenv("FALLBACK_MODEL", ""),
            fallback_url=os.getenv("FALLBACK_URL", ""),
            max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "60000")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "180")),
            data_dir=os.getenv("DATA_DIR", "data"),
        )

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.discord_token:
            problems.append("DISCORD_TOKEN missing")
        if (
            not self.freebuff_key
            and not self.perplexity_key
            and not self.gemini_key
            and not self.fallback_key
            and not self.freebuff_cli
        ):
            problems.append(
                "no LLM provider: set FREEBUFF_CLI=1 or a FREEBUFF_API_KEY / "
                "PERPLEXITY_API_KEY / GEMINI_API_KEY / FALLBACK_API_KEY"
            )
        return problems
