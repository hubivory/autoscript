import sys

PATH = r"C:\Users\jonas\Documents\Default Project\scriptbot\verified_snowy_break_and_steal_an_egg_v2.lua"
OUT = r"C:\Users\jonas\Documents\Default Project\scriptbot\verified_snowy_break_and_steal_an_egg_v3.lua"

src = open(PATH, encoding="utf-8").read()
patches = []

# P1: mirror defaults
patches.append((
    "\tHighlightTarget = false,\n",
    "\tHighlightTarget = false,\n"
    "\tStealAfterKill  = true,\n"
    "\tEvadeGuards     = true,\n",
))

# P2: steal/carry/guard helpers before UI BUILD marker
patches.append((
    "-- ==================== UI BUILD ====================",
    """-- ==================== STEAL / CARRY / GUARD ====================
-- Full loop: break egg -> kill -> hold-E steal prompt -> carry -> evade
-- guardian -> bank at own plot. Every step returns (ok, reason); the farm
-- loop owns all status labels.

local ownPlotCache = nil

local function resolveOwnPlot()
\tif ownPlotCache ~= nil and ownPlotCache.Parent ~= nil then
\t\treturn ownPlotCache
\tend

\tlocal plots = Workspace:FindFirstChild("Plots")
\tif plots == nil then
\t\treturn nil
\tend

\tfor _, plot in ipairs(plots:GetChildren()) do
\t\tlocal ownerId = plot:GetAttribute("OwnerUserId")
\t\tif ownerId ~= nil and tostring(ownerId) == tostring(player.UserId) then
\t\t\townPlotCache = plot
\t\t\treturn plot
\t\tend
\tend

\treturn nil
end

local function isCarrying()
\tlocal count = player:GetAttribute("CarryCount")
\treturn type(count) == "number" and count > 0
end

local function satchelFull()
\tlocal count = player:GetAttribute("CarryCount")
\tlocal cap = player:GetAttribute("SatchelCapacity")
\tif type(cap) ~= "number" then
\t\tcap = 1
\tend
\tif type(count) ~= "number" then
\t\treturn false
\tend
\treturn count >= cap
end

local function snapshotBoard()
\tlocal set = {}
\tfor _, descendant in ipairs(Workspace:GetDescendants()) do
\t\tif descendant:IsA("ProximityPrompt") and descendant.Name == "StealPrompt" then
\t\t\tlocal ok, text = pcall(function()
\t\t\t\treturn tostring(descendant.ObjectText)
\t\t\tend)
\t\t\tif ok then
\t\t\t\tset[text] = true
\t\t\tend
\t\tend
\tend
\treturn set
end

local function anchorPosition()
\tlocal anchor = Workspace:FindFirstChild("PromptAnchor")
\tif anchor == nil then
\t\treturn nil
\tend

\tlocal ok, pos = pcall(function()
\t\treturn anchor.Position
\tend)
\tif ok and typeof(pos) == "Vector3" then
\t\treturn pos
\tend

\tok, pos = pcall(function()
\t\treturn anchor:GetPivot().Position
\tend)
\tif ok and typeof(pos) == "Vector3" then
\t\treturn pos
\tend

\treturn nil
end

local guardianCache = nil

local function guardThreat()
\tlocal guardian = nil
\tif guardianCache ~= nil and guardianCache.Parent ~= nil then
\t\tguardian = guardianCache
\telse
\t\tlocal zoneBuilds = Workspace:FindFirstChild("Build")
\t\tzoneBuilds = zoneBuilds and zoneBuilds:FindFirstChild("ZoneBuilds")
\t\tlocal zone10 = zoneBuilds and zoneBuilds:FindFirstChild("Zone10")
\t\tguardian = zone10 and zone10:FindFirstChild("AlienGuardian")
\t\tif guardian ~= nil then
\t\t\tguardianCache = guardian
\t\tend
\tend

\tif guardian == nil then
\t\treturn false, "no guardian"
\tend

\tlocal state = guardian:GetAttribute("ChaseState")
\tif state ~= nil and state ~= "Roaming" and state ~= "Idle" and state ~= "Returning" then
\t\treturn true, "chased (" .. tostring(state) .. ")"
\tend

\tif guardian:GetAttribute("CaughtUserId") ~= nil and tostring(guardian:GetAttribute("CaughtUserId")) == tostring(player.UserId) then
\t\treturn true, "caught"
\tend

\tlocal character = player.Character
\tlocal root = character and character:FindFirstChild("HumanoidRootPart")
\tif root ~= nil then
\t\tlocal ok, pos = pcall(function()
\t\t\treturn guardian:GetPivot().Position
\t\tend)
\t\tif ok and (pos - root.Position).Magnitude < 200 then
\t\t\treturn true, "guardian close"
\t\tend
\tend

\treturn false, "clear"
end

local function teleportNear(position)
\tlocal now = os.clock()
\tif now - lastTeleport < 3 then
\t\treturn false, "teleport cooling down"
\tend

\tlocal character = player.Character
\tlocal root = character and character:FindFirstChild("HumanoidRootPart")
\tlocal humanoid = character and character:FindFirstChildOfClass("Humanoid")
\tif root == nil or humanoid == nil then
\t\treturn false, "no character"
\tend

\tif humanoid.MoveDirection.Magnitude > 0.1 then
\t\treturn false, "moving"
\tend

\tlastTeleport = now
\tlocal ok = pcall(function()
\t\troot.CFrame = CFrame.new(position + Vector3.new(0, 3, 0))
\tend)

\tif ok then
\t\ttask.wait(1.2)
\t\treturn true, "moved"
\tend
\treturn false, "teleport failed"
end

local function fireStealPrompts(newSet)
\tif type(firesignal) ~= "function" then
\t\treturn 0, "no firesignal"
\tend

\tlocal fired = 0
\tfor _, descendant in ipairs(Workspace:GetDescendants()) do
\t\tif fired >= 3 then
\t\t\tbreak
\t\tend
\t\tif descendant:IsA("ProximityPrompt") and descendant.Name == "StealPrompt" and descendant.Enabled then
\t\t\tif newSet ~= nil then
\t\t\t\tlocal ok, text = pcall(function()
\t\t\t\t\treturn tostring(descendant.ObjectText)
\t\t\t\tend)
\t\t\t\tif not ok or newSet[text] then
\t\t\t\t\tcontinue
\t\t\t\tend
\t\t\tend
\t\t\tpcall(function()
\t\t\t\tfiresignal(descendant.Triggered, player)
\t\t\tend)
\t\t\tfired += 1
\t\t\ttask.wait(0.8)
\t\tend
\tend

\treturn fired, fired > 0 and "fired" or "no live prompt"
end

local function stealSequence(boardBefore)
\tif satchelFull() then
\t\treturn false, "satchel full"
\tend

\tlocal pos = anchorPosition()
\tif pos == nil then
\t\treturn false, "no steal board"
\tend

\tlocal character = player.Character
\tlocal root = character and character:FindFirstChild("HumanoidRootPart")
\tif root == nil then
\t\treturn false, "no character"
\tend

\tif (pos - root.Position).Magnitude > 9 then
\t\tlocal ok, reason = teleportNear(pos)
\t\tif not ok then
\t\t\treturn false, reason
\t\tend
\tend

\tlocal newSet = {}
\tif boardBefore ~= nil then
\t\tfor text, _ in pairs(boardBefore) do
\t\t\tnewSet[text] = true
\t\tend
\tend

\tlocal fired, _ = fireStealPrompts(newSet)
\tif fired == 0 and newSet ~= nil then
\t\tfired, _ = fireStealPrompts(nil)
\tend

\ttask.wait(3)

\tif isCarrying() then
\t\treturn true, "carrying"
\tend

\tif fired == 0 then
\t\treturn false, "no live prompt"
\tend
\treturn false, "steal rejected"
end

local function bankCarry()
\tlocal plot = resolveOwnPlot()
\tif plot == nil then
\t\treturn false, "no home plot"
\tend

\tlocal ok, pivot = pcall(function()
\t\treturn plot:GetPivot().Position
\tend)
\tif not ok then
\t\treturn false, "no plot position"
\tend

\tlocal moved, reason = teleportNear(pivot + Vector3.new(0, 5, 0))
\tif not moved then
\t\treturn false, reason
\tend

\ttask.wait(3)

\tif not isCarrying() then
\t\treturn true, "banked"
\tend

\tlocal rs = game:GetService("ReplicatedStorage")
\tlocal drop = rs:FindFirstChild("DropCarriedRemote")
\tif drop ~= nil and drop:IsA("RemoteEvent") then
\t\tpcall(function()
\t\t\tdrop:FireServer()
\t\tend)
\t\ttask.wait(1.5)
\tend

\tif not isCarrying() then
\t\treturn true, "banked"
\tend
\treturn false, "still carrying"
end

-- ==================== UI BUILD ====================""",
))

# P3a: carry check at loop top (after the isOn gate)
patches.append((
    "\t\tif not isOn(\"AutoFarmEggs\") then\n"
    "\t\t\tfailures = 0\n"
    "\t\t\ttask.wait(0.2)\n"
    "\t\t\tcontinue\n"
    "\t\tend\n",
    "\t\tif not isOn(\"AutoFarmEggs\") then\n"
    "\t\t\tfailures = 0\n"
    "\t\t\ttask.wait(0.2)\n"
    "\t\t\tcontinue\n"
    "\t\tend\n"
    "\n"
    "\t\tif isOn(\"StealAfterKill\") and isCarrying() then\n"
    "\t\t\tif isOn(\"EvadeGuards\") then\n"
    "\t\t\t\tsetLabel(farmStatus, \"Carrying, going home...\")\n"
    "\t\t\t\tlocal banked, breason = bankCarry()\n"
    "\t\t\t\tsetLabel(farmStatus, banked and \"Banked!\" or (\"Bank: \" .. breason))\n"
    "\t\t\telse\n"
    "\t\t\t\tsetLabel(farmStatus, \"Carrying (evade off)\")\n"
    "\t\t\tend\n"
    "\t\t\ttask.wait(1)\n"
    "\t\t\tcontinue\n"
    "\t\tend\n",
))

# P3b: kill -> steal hook in success branch
patches.append((
    "\t\tlocal ok, reason = breakEgg(egg)\n"
    "\n"
    "\t\tif ok then\n"
    "\t\t\tfailures = 0\n"
    "\t\t\tsetLabel(farmStatus, string.format(\"Broke %s on %s via %s\", egg.kind, egg.plot, reason))\n",
    "\t\tlocal boardBefore = nil\n"
    "\t\tif isOn(\"StealAfterKill\") then\n"
    "\t\t\tboardBefore = snapshotBoard()\n"
    "\t\tend\n"
    "\n"
    "\t\tlocal ok, reason = breakEgg(egg)\n"
    "\n"
    "\t\tif ok then\n"
    "\t\t\tfailures = 0\n"
    "\t\t\tsetLabel(farmStatus, string.format(\"Broke %s on %s via %s\", egg.kind, egg.plot, reason))\n"
    "\n"
    "\t\t\tif egg.part.Parent == nil and boardBefore ~= nil then\n"
    "\t\t\t\tlocal carried, sreason = stealSequence(boardBefore)\n"
    "\t\t\t\tif carried then\n"
    "\t\t\t\t\tsetLabel(farmStatus, \"Carrying! Escaping...\")\n"
    "\t\t\t\t\tif isOn(\"EvadeGuards\") then\n"
    "\t\t\t\t\t\tlocal banked, breason = bankCarry()\n"
    "\t\t\t\t\t\tsetLabel(farmStatus, banked and \"Banked!\" or (\"Bank: \" .. breason))\n"
    "\t\t\t\t\telse\n"
    "\t\t\t\t\t\tsetLabel(farmStatus, \"Carrying (evade off)\")\n"
    "\t\t\t\t\tend\n"
    "\t\t\t\telse\n"
    "\t\t\t\t\tsetLabel(farmStatus, \"Kill (\" .. egg.kind .. \"), steal: \" .. sreason)\n"
    "\t\t\t\tend\n"
    "\t\t\tend\n",
))

# P4: UI toggles after HighlightTarget block
patches.append((
    "add(targetSection, \"Toggle\", {\n"
    "\tText     = \"Highlight target\",\n",
    "add(targetSection, \"Toggle\", {\n"
    "\tText     = \"Steal after kill\",\n"
    "\tDefault  = true,\n"
    "\tFlag     = \"StealAfterKill\",\n"
    "\tCallback = function(state)\n"
    "\t\tmirror.StealAfterKill = state\n"
    "\tend,\n"
    "})\n"
    "\n"
    "add(targetSection, \"Toggle\", {\n"
    "\tText     = \"Evade guards\",\n"
    "\tDefault  = true,\n"
    "\tFlag     = \"EvadeGuards\",\n"
    "\tCallback = function(state)\n"
    "\t\tmirror.EvadeGuards = state\n"
    "\tend,\n"
    "})\n"
    "\n"
    "add(targetSection, \"Toggle\", {\n"
    "\tText     = \"Highlight target\",\n",
))

# P5: diagnostics steal bindings
patches.append((
    "\tlocal hitRemote = game:GetService(\"ReplicatedStorage\"):FindFirstChild(\"EggHitRequest\")\n"
    "\tif hitRemote ~= nil and hitRemote:IsA(\"RemoteEvent\") then\n"
    "\t\tbound += 1\n"
    "\telse\n"
    "\t\ttable.insert(unbound, \"egg hit (EggHitRequest)\")\n"
    "\tend\n",
    "\tlocal hitRemote = game:GetService(\"ReplicatedStorage\"):FindFirstChild(\"EggHitRequest\")\n"
    "\tif hitRemote ~= nil and hitRemote:IsA(\"RemoteEvent\") then\n"
    "\t\tbound += 1\n"
    "\telse\n"
    "\t\ttable.insert(unbound, \"egg hit (EggHitRequest)\")\n"
    "\tend\n"
    "\n"
    "\tlocal promptCount = 0\n"
    "\tfor _, descendant in ipairs(Workspace:GetDescendants()) do\n"
    "\t\tif descendant:IsA(\"ProximityPrompt\") and descendant.Name == \"StealPrompt\" and descendant.Enabled then\n"
    "\t\t\tpromptCount += 1\n"
    "\t\tend\n"
    "\tend\n"
    "\tif promptCount > 0 then\n"
    "\t\tbound += 1\n"
    "\telse\n"
    "\t\ttable.insert(unbound, \"steal board (no live prompts)\")\n"
    "\tend\n"
    "\n"
    "\tlocal carryCount = player:GetAttribute(\"CarryCount\")\n"
    "\tlocal satchelCap = player:GetAttribute(\"SatchelCapacity\")\n"
    "\tif type(carryCount) == \"number\" and carryCount > 0 then\n"
    "\t\ttable.insert(unbound, \"carrying (\" .. tostring(carryCount) .. \"/\" .. tostring(satchelCap) .. \")\")\n"
    "\tend\n"
    "\n"
    "\tlocal threat, treason = guardThreat()\n"
    "\tif threat then\n"
    "\t\ttable.insert(unbound, \"guard: \" .. treason)\n"
    "\tend\n",
))

# P6: footer version
patches.append((
    'invoke(win, "SetFooter", string.format("v1.4 | %s | %d", GAME_NAME, player.UserId))',
    'invoke(win, "SetFooter", string.format("v3.0 | %s | %d", GAME_NAME, player.UserId))',
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
