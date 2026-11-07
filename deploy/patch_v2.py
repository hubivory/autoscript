import sys

PATH = r"C:\Users\jonas\Documents\Default Project\scriptbot\verified_snowy_break_and_steal_an_egg.lua"
OUT = r"C:\Users\jonas\Documents\Default Project\scriptbot\verified_snowy_break_and_steal_an_egg_v2.lua"

src = open(PATH, encoding="utf-8").read()
patches = []

T = "\t"

# P1: eggKind nest branch
patches.append((
    'if part.Name == "Egg" then\n'
    '\t\treturn "Normal egg"\n'
    '\tend\n'
    '\n'
    '\treturn nil\n'
    'end\n'
    '\n'
    'local function plotOwner(plot)',
    'if part.Name == "Egg" then\n'
    '\t\treturn "Normal egg"\n'
    '\tend\n'
    '\n'
    '\t-- verified live: nest parts (p1/p2 MeshParts inside *Nest* models)\n'
    '\tif string.find(model.Name, "Nest", 1, true) ~= nil then\n'
    '\t\tif string.find(model.Name, "Gold", 1, true) ~= nil then\n'
    '\t\t\treturn "Gold egg"\n'
    '\t\tend\n'
    '\t\treturn "Normal egg"\n'
    '\tend\n'
    '\n'
    '\treturn nil\n'
    'end\n'
    '\n'
    'local function plotOwner(plot)',
))

# P2: scanEggs calls scanZoneEggs + new function
patches.append((
    '\t\t\ttable.insert(eggs, {\n'
    '\t\t\t\tpart  = descendant,\n'
    '\t\t\t\tkind  = kind,\n'
    '\t\t\t\tplot  = plot.Name,\n'
    '\t\t\t\towner = owner,\n'
    '\t\t\t})\n'
    '\t\tend\n'
    '\tend\n'
    '\n'
    '\treturn #eggs\n'
    'end',
    '\t\t\ttable.insert(eggs, {\n'
    '\t\t\t\tpart  = descendant,\n'
    '\t\t\t\tkind  = kind,\n'
    '\t\t\t\tplot  = plot.Name,\n'
    '\t\t\t\towner = owner,\n'
    '\t\t\t})\n'
    '\t\tend\n'
    '\tend\n'
    '\n'
    '\tscanZoneEggs()\n'
    '\n'
    '\treturn #eggs\n'
    'end\n'
    '\n'
    '-- verified live: eggs live under Workspace.Build.ZoneBuilds.<Zone>.Eggs\n'
    '-- as *Nest* models with p1/p2 MeshParts (not under Workspace.Plots).\n'
    'local function scanZoneEggs()\n'
    '\tlocal builds = Workspace:FindFirstChild("Build")\n'
    '\tif builds == nil then\n'
    '\t\treturn\n'
    '\tend\n'
    '\n'
    '\tlocal zones = builds:FindFirstChild("ZoneBuilds")\n'
    '\tif zones == nil then\n'
    '\t\treturn\n'
    '\tend\n'
    '\n'
    '\tfor _, zone in ipairs(zones:GetChildren()) do\n'
    '\t\tlocal roots = {}\n'
    '\t\tlocal eggFolder = zone:FindFirstChild("Eggs")\n'
    '\t\tif eggFolder ~= nil then\n'
    '\t\t\troots = { eggFolder }\n'
    '\t\telse\n'
    '\t\t\troots = { zone }\n'
    '\t\tend\n'
    '\n'
    '\t\tfor _, root in ipairs(roots) do\n'
    '\t\t\tfor _, descendant in ipairs(root:GetDescendants()) do\n'
    '\t\t\t\tif not descendant:IsA("BasePart") then\n'
    '\t\t\t\t\tcontinue\n'
    '\t\t\t\tend\n'
    '\n'
    '\t\t\t\tlocal kind = eggKind(descendant)\n'
    '\t\t\t\tif kind == nil then\n'
    '\t\t\t\t\tcontinue\n'
    '\t\t\t\tend\n'
    '\n'
    '\t\t\t\ttable.insert(eggs, {\n'
    '\t\t\t\t\tpart  = descendant,\n'
    '\t\t\t\t\tkind  = kind,\n'
    '\t\t\t\t\tplot  = zone.Name,\n'
    '\t\t\t\t\towner = nil,\n'
    '\t\t\t\t})\n'
    '\t\t\tend\n'
    '\t\tend\n'
    '\tend\n'
    'end',
))

# P3: verifiedHit + breakEgg reorder
patches.append((
    'local function breakEgg(egg)\n'
    '\tlocal part = egg.part\n'
    '\tif part == nil or part.Parent == nil then\n'
    '\t\treturn false, "egg gone"\n'
    '\tend\n'
    '\n'
    '\tif not consumeBudget() then\n'
    '\t\treturn false, "request budget full"\n'
    '\tend\n',
    '-- verified live: MasteryPickaxeSwing() + EggHitRequest(part) raises Cash\n'
    '-- (+81k per hit in testing) and yields EggHitLanded. This is the primary\n'
    '-- break path; click/prompt/configured remotes below are fallbacks.\n'
    'local function verifiedHit(part)\n'
    '\tlocal rs = game:GetService("ReplicatedStorage")\n'
    '\tlocal req = rs:FindFirstChild("EggHitRequest")\n'
    '\tif req == nil or not req:IsA("RemoteEvent") then\n'
    '\t\treturn false, "no EggHitRequest"\n'
    '\tend\n'
    '\n'
    '\tif not consumeBudget() then\n'
    '\t\treturn false, "request budget full"\n'
    '\tend\n'
    '\n'
    '\tlocal swing = rs:FindFirstChild("MasteryPickaxeSwing")\n'
    '\tif swing ~= nil and swing:IsA("RemoteEvent") then\n'
    '\t\tif consumeBudget() then\n'
    '\t\t\tpcall(function()\n'
    '\t\t\t\tswing:FireServer()\n'
    '\t\t\tend)\n'
    '\t\tend\n'
    '\t\ttask.wait(0.35)\n'
    '\tend\n'
    '\n'
    '\tlocal ok = pcall(function()\n'
    '\t\treq:FireServer(part)\n'
    '\tend)\n'
    '\treturn ok, ok and "egg hit" or "egg hit failed"\n'
    'end\n'
    '\n'
    'local function breakEgg(egg)\n'
    '\tlocal part = egg.part\n'
    '\tif part == nil or part.Parent == nil then\n'
    '\t\treturn false, "egg gone"\n'
    '\tend\n'
    '\n'
    '\tlocal hitOk, hitReason = verifiedHit(part)\n'
    '\tif hitOk then\n'
    '\t\treturn true, hitReason\n'
    '\tend\n'
    '\tif hitReason == "request budget full" then\n'
    '\t\treturn false, hitReason\n'
    '\tend\n'
    '\n'
    '\tif not consumeBudget() then\n'
    '\t\treturn false, "request budget full"\n'
    '\tend\n',
))

# P4: teleportToEgg + travelToEgg before UI BUILD marker
patches.append((
    '\tlastTeleport = now\n'
    '\tlocal ok = pcall(function()\n'
    '\t\troot.CFrame = CFrame.new(spawnPoint.Position + Vector3.new(0, 3, 0))\n'
    '\tend)\n'
    '\n'
    '\tif ok then\n'
    '\t\treturn true, "moved to " .. plotName\n'
    '\tend\n'
    '\treturn false, "teleport failed"\n'
    'end\n'
    '\n'
    '-- ==================== UI BUILD ====================',
    '\tlastTeleport = now\n'
    '\tlocal ok = pcall(function()\n'
    '\t\troot.CFrame = CFrame.new(spawnPoint.Position + Vector3.new(0, 3, 0))\n'
    '\tend)\n'
    '\n'
    '\tif ok then\n'
    '\t\treturn true, "moved to " .. plotName\n'
    '\tend\n'
    '\treturn false, "teleport failed"\n'
    'end\n'
    '\n'
    'local function teleportToEgg(egg)\n'
    '\tlocal now = os.clock()\n'
    '\tif now - lastTeleport < 3 then\n'
    '\t\treturn false, "teleport cooling down"\n'
    '\tend\n'
    '\n'
    '\tlocal part = egg.part\n'
    '\tif part == nil or part.Parent == nil then\n'
    '\t\treturn false, "egg gone"\n'
    '\tend\n'
    '\n'
    '\tlocal character = player.Character\n'
    '\tlocal root = character and character:FindFirstChild("HumanoidRootPart")\n'
    '\tlocal humanoid = character and character:FindFirstChildOfClass("Humanoid")\n'
    '\tif root == nil or humanoid == nil then\n'
    '\t\treturn false, "no character"\n'
    '\tend\n'
    '\n'
    '\tif humanoid.MoveDirection.Magnitude > 0.1 then\n'
    '\t\treturn false, "moving"\n'
    '\tend\n'
    '\n'
    '\tlastTeleport = now\n'
    '\tlocal ok = pcall(function()\n'
    '\t\troot.CFrame = CFrame.new(part.Position + Vector3.new(0, 4, 6))\n'
    '\tend)\n'
    '\n'
    '\tif ok then\n'
    '\t\ttask.wait(0.6)\n'
    '\t\treturn true, "moved to egg"\n'
    '\tend\n'
    '\treturn false, "teleport failed"\n'
    'end\n'
    '\n'
    '-- eggs can be thousands of studs away: teleport when far, walk when near.\n'
    'local function travelToEgg(egg, distance)\n'
    '\tif distance <= 7 then\n'
    '\t\treturn true, "in range"\n'
    '\tend\n'
    '\n'
    '\tif distance > 60 then\n'
    '\t\treturn teleportToEgg(egg)\n'
    '\tend\n'
    '\n'
    '\tif approachEgg(egg) then\n'
    '\t\treturn true, "walked to egg"\n'
    '\tend\n'
    '\treturn false, "could not reach egg"\n'
    'end\n'
    '\n'
    '-- ==================== UI BUILD ====================',
))

# P5: farm loop travel
patches.append((
    '\t\tif isOn("ApproachEggs") and distance > 7 then\n'
    '\t\t\tif not approachEgg(egg) then\n'
    '\t\t\t\tsetLabel(farmStatus, "Could not reach egg")\n'
    '\t\t\t\ttask.wait(0.5)\n'
    '\t\t\t\tcontinue\n'
    '\t\t\tend\n'
    '\t\tend',
    '\t\tif isOn("ApproachEggs") and distance > 7 then\n'
    '\t\t\tlocal reached, travelReason = travelToEgg(egg, distance)\n'
    '\t\t\tif not reached then\n'
    '\t\t\t\tsetLabel(farmStatus, "Travel: " .. travelReason)\n'
    '\t\t\t\ttask.wait(0.5)\n'
    '\t\t\t\tcontinue\n'
    '\t\t\tend\n'
    '\t\tend',
))

# P6: button travel
patches.append((
    '\t\tif isOn("ApproachEggs") and distance > 7 then\n'
    '\t\t\tapproachEgg(egg)\n'
    '\t\tend\n'
    '\n'
    '\t\tlocal ok, reason = breakEgg(egg)',
    '\t\tif isOn("ApproachEggs") and distance > 7 then\n'
    '\t\t\tlocal reached, travelReason = travelToEgg(egg, distance)\n'
    '\t\t\tif not reached then\n'
    '\t\t\t\tsetLabel(actionStatus, "Travel: " .. travelReason)\n'
    '\t\t\t\treturn\n'
    '\t\t\tend\n'
    '\t\tend\n'
    '\n'
    '\t\tlocal ok, reason = breakEgg(egg)',
))

# P7: MaxDistance defaults + slider range
for old, new in [
    ("\tMaxDistance     = 250,", "\tMaxDistance     = 2500,"),
    ('local limit = numberFlag("MaxDistance", 250)', 'local limit = numberFlag("MaxDistance", 2500)'),
    ("\tMax      = 1000,", "\tMax      = 5000,"),
    ("\tDefault  = 250,", "\tDefault  = 2500,"),
    ("mirror.MaxDistance = tonumber(value) or 250", "mirror.MaxDistance = tonumber(value) or 2500"),
]:
    patches.append((old, new))

# P8: tab icons
patches.append((
    'local function tab(name)\n'
    '\tlocal ok, result = pcall(function()\n'
    '\t\treturn win:Tab({ Name = name })\n'
    '\tend)',
    'local TAB_ICONS = {\n'
    '\tMain            = "house",\n'
    '\tPlayer          = "user",\n'
    '\tInfo            = "info",\n'
    '\tDiagnostics     = "wrench",\n'
    '\t["UI Settings"] = "gear",\n'
    '}\n'
    '\n'
    'local function tab(name)\n'
    '\tlocal ok, result = pcall(function()\n'
    '\t\treturn win:Tab({ Name = name, Icon = TAB_ICONS[name] })\n'
    '\tend)',
))

# P9: visibility bump before final notify
patches.append((
    'notify("Auto farm ready. Press Auto farm eggs to start.", "success", 6)\n'
    'print(GAME_NAME .. " loaded")',
    '-- keep the panel on top and visible for whoever runs the script.\n'
    'pcall(function()\n'
    '\tlocal holder = (gethui and gethui()) or game:GetService("CoreGui")\n'
    '\tfor _, gui in ipairs(holder:GetChildren()) do\n'
    '\t\tif gui:IsA("ScreenGui") then\n'
    '\t\t\tfor _, descendant in ipairs(gui:GetDescendants()) do\n'
    '\t\t\t\tif (descendant:IsA("TextLabel") or descendant:IsA("TextButton")) and descendant.Text == "Snowy Studios" then\n'
    '\t\t\t\t\tgui.DisplayOrder = 999\n'
    '\t\t\t\t\tgui.Enabled = true\n'
    '\t\t\t\t\tbreak\n'
    '\t\t\t\tend\n'
    '\t\t\tend\n'
    '\t\tend\n'
    '\tend\n'
    'end)\n'
    '\n'
    'notify("Auto farm ready. Press Auto farm eggs to start.", "success", 6)\n'
    'print(GAME_NAME .. " loaded")',
))

# P10: diagnostics binding for the verified hit path
patches.append((
    '\tif resolveBreakRemote() ~= nil then\n'
    '\t\tbound += 1\n'
    '\telse\n'
    '\t\ttable.insert(unbound, "named break remote")\n'
    '\tend',
    '\tif resolveBreakRemote() ~= nil then\n'
    '\t\tbound += 1\n'
    '\telse\n'
    '\t\ttable.insert(unbound, "named break remote")\n'
    '\tend\n'
    '\n'
    '\tlocal hitRemote = game:GetService("ReplicatedStorage"):FindFirstChild("EggHitRequest")\n'
    '\tif hitRemote ~= nil and hitRemote:IsA("RemoteEvent") then\n'
    '\t\tbound += 1\n'
    '\telse\n'
    '\t\ttable.insert(unbound, "egg hit (EggHitRequest)")\n'
    '\tend',
))

for i, (old, new) in enumerate(patches):
    count = src.count(old)
    if count != 1:
        print(f"patch {i}: found {count}x, ABORT")
        sys.exit(1)
    src = src.replace(old, new, 1)
    print(f"patch {i}: ok")

open(OUT, "w", encoding="utf-8", newline="").write(src)
print("wrote", OUT, len(src), "chars")
