import os
import pty
import re
import select
import sys
import time

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip(data: bytes) -> str:
    text = data.decode("utf-8", "replace")
    return ANSI_RE.sub("", text)


def read_until(fd: int, needle: str, timeout: float) -> bytes:
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        ready, _, _ = select.select([fd], [], [], 0.5)
        if ready:
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            if needle.encode() in buf:
                break
    return buf


def main() -> int:
    workdir = "/tmp/fbcli_work"
    os.makedirs(workdir, exist_ok=True)
    binary = "/tmp/fbcli/node_modules/.bin/freebuff"
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(workdir)
        os.execv(binary, [binary])
        os._exit(1)
    try:
        out = read_until(fd, "Enter a coding task", 60)
        print("=== boot (stripped tail) ===")
        print(strip(out)[-1500:])
        os.write(fd, b"say OK\r")
        time.sleep(45)
        rest = b""
        while True:
            ready, _, _ = select.select([fd], [], [], 1.0)
            if not ready:
                break
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            rest += chunk
            if len(rest) > 200000:
                break
        print("=== reply (stripped tail) ===")
        print(strip(rest)[-3000:])
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.kill(pid, 9)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
