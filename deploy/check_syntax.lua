local path = arg and arg[1] or "/tmp/attempt2_script.lua"
local fn, err = loadfile(path)
if fn then
  print("COMPILES")
else
  print("SYNTAX ERROR: " .. tostring(err))
end
