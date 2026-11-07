import subprocess
import time

SOCK = "fbmodel2"
BIN = "/home/ubuntu/.nvm/versions/node/v20.20.2/bin/freebuff"
WORK = "/tmp/fbcli_work"


def tmux(*args: str) -> str:
    proc = subprocess.run(
        ["tmux", "-L", SOCK, *args], capture_output=True, text=True, timeout=30
    )
    return proc.stdout


def pane(scroll: int = 100) -> str:
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
time.sleep(5)
tmux("send-keys", "-t", "fb", "-l", "deepseek-v4-pro")
time.sleep(4)
out = pane(100)
print("=========== PANE ===========")
print(out[-3000:])
tmux("kill-server")
