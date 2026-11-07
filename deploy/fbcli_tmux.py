import re
import subprocess
import sys
import time

SOCK = "fbproto2"
BIN = "/tmp/fbcli/node_modules/.bin/freebuff"
WORK = "/tmp/fbcli_work"


def tmux(*args: str) -> str:
    proc = subprocess.run(
        ["tmux", "-L", SOCK, *args], capture_output=True, text=True, timeout=30
    )
    return proc.stdout


def pane(scroll: int = 400) -> str:
    return tmux("capture-pane", "-t", "fb", "-p", "-S", f"-{scroll}")


def wait_for(text: str, timeout: float) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if text in pane(60):
            return True
        time.sleep(2)
    return False


def main() -> int:
    prompt = sys.argv[1] if len(sys.argv) > 1 else "say OK"
    tmux("kill-server")
    time.sleep(1)
    tmux(
        "new-session", "-d", "-s", "fb", "-x", "140", "-y", "50",
        BIN, "--trust-agents", "--cwd", WORK,
    )
    if not wait_for("Enter a coding task", 90):
        print("BOOT TIMEOUT")
        print(pane(60)[-2000:])
        tmux("kill-server")
        return 1
    print("booted")
    tmux("send-keys", "-t", "fb", "-l", prompt)
    time.sleep(1)
    tmux("send-keys", "-t", "fb", "Enter")
    deadline = time.time() + 180
    last = ""
    stable = 0
    final = ""
    while time.time() < deadline:
        time.sleep(8)
        try:
            current = pane(500)
        except Exception:
            break
        if current == last:
            stable += 1
        else:
            stable = 0
        last = current
        if stable >= 2 and "Enter a coding task" in current:
            final = current
            break
    else:
        final = last
    print("=== FINAL PANE (last 4000 chars) ===")
    print(final[-4000:])
    tmux("kill-server")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
