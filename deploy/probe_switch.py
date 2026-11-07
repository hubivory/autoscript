import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_cli import FreebuffCLIClient


def main() -> int:
    client = FreebuffCLIClient(timeout=120)
    import subprocess
    import uuid

    sock = f"fbsw{uuid.uuid4().hex[:8]}"
    client._tmux(sock, "kill-server")
    time.sleep(0.5)
    client._tmux(
        sock, "new-session", "-d", "-s", "fb", "-x", "140", "-y", "50",
        client.binary, "--trust-agents", "--cwd", client.workdir,
    )
    os.makedirs(client.workdir, exist_ok=True)
    if not client._wait_for(sock, "Enter a coding task", 120):
        print("BOOT FAIL")
        client._tmux(sock, "kill-server")
        return 1
    print("booted")
    actual = client._select_model(sock, "Opus")
    print("ACTUAL:", repr(actual))
    client._tmux(sock, "kill-server")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
