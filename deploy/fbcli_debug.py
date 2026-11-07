import subprocess
import time

BIN = "/home/ubuntu/.nvm/versions/node/v20.20.2/bin/freebuff"
SOCK = "fbdebug"


def tmux(*args: str) -> str:
    proc = subprocess.run(
        ["tmux", "-L", SOCK, *args], capture_output=True, text=True, timeout=30
    )
    return proc.stdout + proc.stderr


print(tmux("kill-server"))
time.sleep(1)
print(tmux("new-session", "-d", "-s", "fb", "-x", "140", "-y", "50",
           BIN, "--trust-agents", "--cwd", "/tmp/fbcli_work"))
time.sleep(25)
print("=========== PANE ===========")
print(tmux("capture-pane", "-t", "fb", "-p", "-S", "-200"))
tmux("kill-server")
