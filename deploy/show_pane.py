import re

src = open(
    "/home/ubuntu/scriptbot/data/fbcli_work/last_pane.txt",
    encoding="utf-8",
    errors="replace",
).read()
src = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", src)
src = re.sub(r"\x1b\][^\x07]*\x07", "", src)
print(src[-2500:])
