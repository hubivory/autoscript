path = "/tmp/attempt2_script.lua"
src = open(path, encoding="utf-8").read()
old = "\treturn #eggs\nend\n\nlocal function distanceTo(part)"
new = (
    "\treturn #eggs\n"
    "end\n"
    "\n"
    "local function countGoldEggs()\n"
    "\tlocal count = 0\n"
    "\tfor _, egg in ipairs(eggs) do\n"
    "\t\tif egg.kind == \"Gold egg\" and egg.part.Parent ~= nil then\n"
    "\t\t\tcount = count + 1\n"
    "\t\tend\n"
    "\tend\n"
    "\treturn count\n"
    "end\n"
    "\n"
    "local function distanceTo(part)"
)
assert src.count(old) == 1, "anchor not unique"
open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
print("patched")
