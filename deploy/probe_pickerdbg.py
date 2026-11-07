import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_cli import FreebuffCLIClient, strip_ansi


def main() -> int:
    client = FreebuffCLIClient(timeout=120)
    import uuid

    sock = f"fbdbg{uuid.uuid4().hex[:8]}"
    client._tmux(sock, "kill-server")
    time.sleep(0.5)
    client._tmux(
        sock, "new-session", "-d", "-s", "fb", "-x", "140", "-y", "50",
        client.binary, "--trust-agents", "--cwd", client.workdir,
    )
    os.makedirs(client.workdir, exist_ok=True)
    print("booted:", client._wait_for(sock, "Enter a coding task", 120))
    client._tmux(sock, "send-keys", "-t", "fb", "-l", "/model")
    time.sleep(1)
    client._tmux(sock, "send-keys", "-t", "fb", "Enter")
    time.sleep(8)
    pane = strip_ansi(client._pane(sock, 150))
    print("has choose-model:", "choose model" in pane)
    print("has picker rows:", bool(re.search(r"\d+x\b", pane)))
    for line in pane.splitlines():
        if "choose model" in line or "›" in line:
            print("PICKER:", line.strip()[:120])
    client._tmux(sock, "kill-server")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
