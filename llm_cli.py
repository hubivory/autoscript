from __future__ import annotations

import asyncio
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid

from llm import LLMError, OutOfCredits

BEGIN = "@@BEGIN@@"
END = "@@END@@"

ANSI_RE = re.compile(
    r"\x1b\[[0-9;?]*[a-zA-Z]"
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    r"|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)

CHROME_RES = [
    re.compile(r"Ad \[Report"),
    re.compile(r"End session"),
    re.compile(r"for history"),
    re.compile(r"/model to change"),
    re.compile(r"Enter a coding task"),
    re.compile(r"Try one of these"),
    re.compile(r"^\s*→"),
    re.compile(r"1h left"),
    re.compile(r"Refer friends"),
    re.compile(r"Copy invite link"),
    re.compile(r"Try Exa"),
    re.compile(r"^\[\d+:\d+ [AP]M\]"),
    re.compile(r"Press ENTER"),
    re.compile(r"Your first message starts the session"),
    re.compile(r"Some models aren.?t available"),
    re.compile(r"Chat: (New chat|.*)"),
    re.compile(r"• \d+s •"),
    re.compile(r"^\s*[⎘△▽•]\s*$"),
]

FAIL_RES = [
    re.compile(r"rate.?limit", re.IGNORECASE),
    re.compile(r"too many requests", re.IGNORECASE),
    re.compile(r"something went wrong", re.IGNORECASE),
    re.compile(r"session (expired|invalid)", re.IGNORECASE),
    re.compile(r"not logged in", re.IGNORECASE),
]


def strip_ansi(data: str) -> str:
    return ANSI_RE.sub("", data)


def clean_lines(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if all(ch in "│╭╰╮╯─ " for ch in stripped):
            continue
        if any(rx.search(line) for rx in CHROME_RES):
            continue
        out.append(line.rstrip())
    return out


def extract_answer(pane_text: str) -> str:
    text = strip_ansi(pane_text)
    end = text.rfind(END)
    start = text.rfind(BEGIN, 0, end) if end != -1 else -1
    if start != -1 and end != -1 and end > start:
        return text[start + len(BEGIN) : end].strip()
    lines = clean_lines(text)
    return "\n".join(lines[-120:]).strip()


def failure_hint(pane_text: str) -> str | None:
    text = strip_ansi(pane_text)
    for rx in FAIL_RES:
        match = rx.search(text)
        if match:
            i = max(0, match.start() - 120)
            return text[i : match.end() + 120].strip()
    return None


def status_model(pane_text: str) -> str:
    text = strip_ansi(pane_text)
    found = ""
    for line in text.splitlines():
        if "/model to change" in line:
            head = line.split("•")[0]
            head = re.sub(r"[^A-Za-z0-9 .\-/()+]", "", head).strip(" /")
            if head:
                found = head
    return found


def row_matches(pane_text: str, filt: str) -> bool:
    text = strip_ansi(pane_text).lower()
    needle = filt.lower()
    hits = 0
    for line in text.splitlines():
        if needle not in line:
            continue
        if "enter a coding task" in line:
            continue
        if "1x" in line or "2x" in line or "3x" in line or "•" in line or "›" in line:
            hits += 1
    return hits >= 1


class FreebuffCLIClient:
    """Drive the official FreeBuff CLI (user's own login) through tmux."""

    def __init__(
        self,
        binary: str = "",
        workdir: str = "",
        model: str = "",
        timeout: int = 600,
    ) -> None:
        self.binary = (
            binary
            or shutil.which("freebuff")
            or "/home/ubuntu/.nvm/versions/node/v20.20.2/bin/freebuff"
        )
        self.workdir = workdir or tempfile.mkdtemp(prefix="fbcli_")
        self.model = model
        self.timeout = timeout
        self.last_provider = ""
        self.last_model_actual = ""
        self._lock = asyncio.Lock()

    def _tmux(self, sock: str, *args: str) -> str:
        try:
            proc = subprocess.run(
                ["tmux", "-L", sock, *args],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise LLMError(f"tmux unavailable: {exc}") from exc
        return proc.stdout

    def _pane(self, sock: str, scroll: int = 600) -> str:
        return self._tmux(sock, "capture-pane", "-t", "fb", "-p", "-S", f"-{scroll}")

    def _wait_for(self, sock: str, text: str, timeout: float) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                if text in self._pane(sock, 60):
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def _build_prompt_file(self, messages: list[dict]) -> str:
        parts: list[str] = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                )
            parts.append(f"# {role.upper()}\n{content}")
        path = os.path.join(self.workdir, "prompt.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n\n".join(parts) + "\n")
        return path

    def _select_model(self, sock: str, filt: str) -> str:
        self._tmux(sock, "send-keys", "-t", "fb", "-l", "/model")
        time.sleep(1)
        self._tmux(sock, "send-keys", "-t", "fb", "Enter")
        if not self._wait_for(sock, "choose model", 25):
            return ""
        self._tmux(sock, "send-keys", "-t", "fb", "-l", filt)
        time.sleep(4)
        try:
            pane = self._pane(sock, 200)
        except Exception:
            pane = ""
        if not row_matches(pane, filt):
            self._tmux(sock, "send-keys", "-t", "fb", "Escape")
            time.sleep(1)
            for _ in range(len(filt) + 6):
                self._tmux(sock, "send-keys", "-t", "fb", "BSpace")
                time.sleep(0.03)
            time.sleep(1)
            return ""
        self._tmux(sock, "send-keys", "-t", "fb", "Enter")
        time.sleep(6)
        try:
            return status_model(self._pane(sock, 60))
        except Exception:
            return ""

    def _run_once(self, messages: list[dict], model: str | None, max_tokens: int) -> str:
        if not self.binary or not os.path.exists(self.binary):
            raise LLMError("freebuff CLI binary not found")
        os.makedirs(self.workdir, exist_ok=True)
        self._build_prompt_file(messages)
        prompt_path = os.path.join(self.workdir, "prompt.md")
        with open(prompt_path, "rb") as handle:
            digest = hashlib.sha1(handle.read()).hexdigest()[:8]
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sock = f"fbcli{uuid.uuid4().hex[:8]}"
        sent = (
            f"[task {digest} @ {stamp}] Read the file prompt.md in the working "
            "directory and follow its instructions exactly. Do not run shell "
            "commands. Do not create, edit, or delete files. Do not ask "
            "questions. Write your complete answer directly in the chat, "
            f"starting with a line containing only {BEGIN} "
            f"and ending with a line containing only {END}."
        )
        try:
            self._tmux(sock, "kill-server")
            time.sleep(0.5)
            self._tmux(
                sock, "new-session", "-d", "-s", "fb", "-x", "140", "-y", "50",
                self.binary, "--trust-agents", "--cwd", self.workdir,
            )
            self._tmux(sock, "set-option", "-w", "-t", "fb", "history-limit", "20000")
            _ = prompt_path
            _ = max_tokens
            if not self._wait_for(sock, "Enter a coding task", 120):
                raise LLMError("freebuff CLI did not boot")
            want = (model or self.model or "").strip()
            self.last_model_actual = ""
            if want:
                try:
                    self.last_model_actual = self._select_model(sock, want)
                except Exception:
                    self.last_model_actual = ""
            self._tmux(sock, "send-keys", "-t", "fb", "-l", sent)
            time.sleep(1)
            self._tmux(sock, "send-keys", "-t", "fb", "Enter")
            deadline = time.time() + self.timeout
            last = ""
            stable = 0
            final = ""
            started = time.time()
            while time.time() < deadline:
                time.sleep(8)
                try:
                    current = self._pane(sock, 20000)
                except Exception:
                    break
                if current == last:
                    stable += 1
                else:
                    stable = 0
                last = current
                if (
                    stable >= 3
                    and time.time() - started > 45
                    and "Enter a coding task" in current
                ):
                    final = current
                    break
            else:
                final = last
            if not final:
                raise LLMError("freebuff CLI produced no output")
            try:
                with open(
                    os.path.join(self.workdir, "last_pane.txt"), "w", encoding="utf-8"
                ) as handle:
                    handle.write(final)
            except OSError:
                pass
            hint = failure_hint(final)
            if hint:
                raise LLMError(f"freebuff CLI reported a failure: {hint[:400]}")
            answer = extract_answer(final)
            if not answer:
                raise LLMError("could not parse an answer from freebuff CLI output")
            return answer
        finally:
            try:
                self._tmux(sock, "kill-server")
            except Exception:
                pass

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 8192,
    ) -> str:
        async with self._lock:
            text = await asyncio.to_thread(self._run_once, messages, model, max_tokens)
            self.last_provider = "freebuff-cli"
            return text
