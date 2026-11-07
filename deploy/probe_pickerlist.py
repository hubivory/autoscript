import subprocess
import time

SOCK = "fbmodels"
BIN = "/home/ubuntu/.nvm/versions/node/v20.20.2/bin/freebuff"
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
        try:
            if text in pane(40):
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


tmux("kill-server")
time.sleep(1)
tmux("new-session", "-d", "-s", "fb", "-x", "140", "-y", "50",
     BIN, "--trust-agents", "--cwd", WORK)
print("booted:", wait_for("Enter a coding task", 120))
tmux("send-keys", "-t", "fb", "-l", "/model")
time.sleep(1)
tmux("send-keys", "-t", "fb", "Enter")
time.sleep(8)
with open("/tmp/picker_full.txt", "w") as handle:
    handle.write(pane(800))
print("saved")
tmux("kill-server")
