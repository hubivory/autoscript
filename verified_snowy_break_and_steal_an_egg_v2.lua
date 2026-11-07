--// Snowy - Break and Steal an Egg

-- ==================== BOOT ====================

pcall(function()
	local unload = getgenv().SnowyStudiosUnload
	if type(unload) == "function" then
		unload()
	end
end)

repeat
	task.wait()
until game:IsLoaded()

local SNOWY_FETCH =
	"https://raw.githubusercontent.com/0x1s2s/Snowy-Ui-Library/refs/heads/main/SnowyUi"
local SNOWY_FETCH_ALT =
	"https://cdn.jsdelivr.net/gh/0x1s2s/Snowy-Ui-Library@main/SnowyUi"

local function snowyLooksReal(t)
	return type(t) == "table" and type(t.Window) == "function"
end

local function tryFetch(url)
	local got
	local ok, res = pcall(function()
		return loadstring(game:HttpGet(url))()
	end)
	if ok and type(res) == "table" then
		got = res
	end
	if not got then
		local fn = request or http_request or (syn and syn.request)
		if fn then
			local ok2, res2 = pcall(function()
				local r = fn({ Url = url, Method = "GET" })
				local src = type(r) == "table" and (r.Body or r.body) or r
				if type(src) == "string" then
					return loadstring(src)()
				end
			end)
			if ok2 and type(res2) == "table" then
				got = res2
			end
		end
	end
	return got
end

local snowy = tryFetch(SNOWY_FETCH)
if not snowyLooksReal(snowy) then
	snowy = tryFetch(SNOWY_FETCH_ALT)
end
if not snowyLooksReal(snowy) then
	error("[Snow Hub] Failed to fetch library.")
end

-- ==================== DISK CACHE ====================

do
	pcall(makefolder, "SnowyStudios")

	local cached = false
	if type(isfile) == "function" then
		local ok, present = pcall(isfile, "SnowyStudios/Library.lua")
		cached = ok and present == true
	end

	if not cached and type(writefile) == "function" then
		pcall(function()
			writefile("SnowyStudios/Library.lua", game:HttpGet(SNOWY_FETCH))
		end)
	end
end

-- ==================== ADAPTER ====================

local activeRawWin = nil

getgenv().__SnowHubAdapter = snowy
getgenv().Snowy = snowy

local function notifyAdapter(content, ntype, dur)
	local payload

	if type(content) == "table" then
		payload = {
			Title    = content.Title or "Snowy Studios",
			Text     = content.Text or content.Content or content.Description or "",
			Type     = content.Type or ntype or "info",
			Duration = content.Duration or dur or 4,
		}
	else
		payload = {
			Title    = "Snowy Studios",
			Text     = tostring(content),
			Type     = ntype or "info",
			Duration = dur or 4,
		}
	end

	if activeRawWin ~= nil then
		local ok = pcall(function()
			activeRawWin:Notify(payload)
		end)
		if ok then
			return true
		end
	end

	return (pcall(function()
		snowy:Notify(payload)
	end))
end

local Library = getgenv().__SnowHubAdapter
local Flags = Library.Flags or {}

-- ==================== SERVICES ====================

local Players = game:GetService("Players")
local Workspace = workspace

local GAME_NAME = "Break and Steal an Egg"
local PLACE_ID = 114326934417838

local player = Players.LocalPlayer
local JOB_ID = tostring(game.JobId)

-- ==================== STATE ====================

local alive = true
local generation = 0
local connections = {}
local startedAt = os.clock()
local unload

local mirror = {
	AutoFarmEggs    = false,
	ApproachEggs    = true,
	EggScope        = "All plots",
	EggFilter       = "Any egg",
	BreakDelay      = 0.45,
	MaxDistance     = 2500,
	SafeMode        = true,
	MaxRequests     = 3,
	OverrideMovement = false,
	WalkSpeed       = 16,
	JumpPower       = 50,
	FieldOfView     = 70,
	HideGameHud     = false,
	HighlightTarget = false,
	Notifications   = true,
	MyPlot          = "",
	BreakRemoteName = "",
	AllowRemoteTest = false,
	MenuKeybind     = "RightControl",
	CandidatePath   = "",
}

-- ==================== FLAG HELPERS ====================

local function flagStore()
	local store = Library and Library.Flags
	if type(store) == "table" then
		return store
	end
	return Flags
end

local function rawFlag(flag)
	local store = flagStore()
	local holder = store and store[flag]

	if type(holder) == "table" then
		if holder.Value ~= nil then
			return holder.Value
		end
		return mirror[flag]
	end

	if holder ~= nil then
		return holder
	end

	return mirror[flag]
end

local function isOn(flag)
	return rawFlag(flag) == true
end

local function numberFlag(flag, fallback)
	local value = tonumber(rawFlag(flag))
	if value ~= nil then
		return value
	end
	if fallback ~= nil then
		return fallback
	end
	local stored = tonumber(mirror[flag])
	if stored ~= nil then
		return stored
	end
	return 0
end

local function stringFlag(flag, fallback)
	local value = rawFlag(flag)
	if type(value) == "string" then
		return value
	end
	if fallback ~= nil then
		return fallback
	end
	local stored = mirror[flag]
	if type(stored) == "string" then
		return stored
	end
	return ""
end

local function forceOff(flag)
	local store = Library and Library.Flags
	local holder = store and store[flag]
	if type(holder) == "table" and holder.Value ~= nil then
		pcall(function()
			holder.Value = false
		end)
	end
	mirror[flag] = false
end

-- ==================== UI / SCRIPT HELPERS ====================

-- The library is fetched at runtime and its surface may drift between builds.
-- Every call into it goes through here so a renamed method cannot abort the load.
local function invoke(owner, method, arg)
	if owner == nil then
		return nil
	end

	local fn = owner[method]
	if type(fn) ~= "function" then
		return nil
	end

	local ok, result = pcall(fn, owner, arg)
	if ok then
		return result
	end
	return nil
end

local labelText = {}

local function setLabel(handle, text)
	if handle == nil then
		return
	end

	if type(text) ~= "string" then
		text = tostring(text)
	end

	if labelText[handle] == text then
		return
	end
	labelText[handle] = text

	if typeof(handle) == "Instance" then
		local textLabel = handle
		if not textLabel:IsA("TextLabel") then
			textLabel = handle:FindFirstChildWhichIsA("TextLabel", true)
		end
		if textLabel ~= nil then
			pcall(function()
				textLabel.Text = text
			end)
		end
		return
	end

	for _, method in ipairs({ "SetText", "Set", "Update", "SetLabel" }) do
		local fn = handle[method]
		if type(fn) == "function" then
			local ok = pcall(fn, handle, text)
			if ok then
				return
			end
		end
	end
end

local function notify(text, ntype, duration)
	if not isOn("Notifications") then
		return
	end
	notifyAdapter({ Text = text, Type = ntype or "info", Duration = duration or 4 })
end

local function track(connection)
	if connection ~= nil then
		table.insert(connections, connection)
	end
	return connection
end

local function isCurrentInstance(gen)
	return alive and gen == generation
end

local pressTimes = {}

local function allowPress(name, window)
	local now = os.clock()
	local last = pressTimes[name]
	if last ~= nil and now - last < (window or 0.5) then
		return false
	end
	pressTimes[name] = now
	return true
end

local function formatDuration(seconds)
	local total = math.floor(seconds)
	return string.format("%d:%02d:%02d", total // 3600, (total % 3600) // 60, total % 60)
end

local function readLeaderstat(name)
	local folder = player:FindFirstChild("leaderstats")
	local value = folder and folder:FindFirstChild(name)

	if value ~= nil then
		return tostring(value.Value)
	end

	local attribute = player:GetAttribute(name)
	if attribute ~= nil then
		return tostring(attribute)
	end

	return "--"
end

-- ==================== MOVEMENT / VIEW ====================

local defaultMovement = { walkSpeed = 16, jumpPower = 50 }
local defaultFov = 70
local originalMovement = nil
local originalFov = nil

local function currentHumanoid()
	local character = player.Character
	if character == nil then
		return nil
	end
	return character:FindFirstChildOfClass("Humanoid")
end

local function applyMovement()
	local humanoid = currentHumanoid()
	if humanoid == nil then
		return
	end

	if originalMovement == nil or originalMovement.humanoid ~= humanoid then
		originalMovement = {
			humanoid  = humanoid,
			walkSpeed = humanoid.WalkSpeed,
			jumpPower = humanoid.JumpPower,
		}
	end

	if isOn("OverrideMovement") then
		humanoid.WalkSpeed = math.clamp(numberFlag("WalkSpeed", 16), 8, 80)
		humanoid.JumpPower = math.clamp(numberFlag("JumpPower", 50), 0, 120)
	else
		humanoid.WalkSpeed = originalMovement.walkSpeed or defaultMovement.walkSpeed
		humanoid.JumpPower = originalMovement.jumpPower or defaultMovement.jumpPower
	end
end

local function restoreMovement()
	local humanoid = currentHumanoid()
	if humanoid == nil then
		return
	end

	local walkSpeed = defaultMovement.walkSpeed
	local jumpPower = defaultMovement.jumpPower
	if originalMovement ~= nil and originalMovement.humanoid == humanoid then
		walkSpeed = originalMovement.walkSpeed or walkSpeed
		jumpPower = originalMovement.jumpPower or jumpPower
	end

	pcall(function()
		humanoid.WalkSpeed = walkSpeed
		humanoid.JumpPower = jumpPower
	end)
end

local function applyFieldOfView()
	local camera = Workspace.CurrentCamera
	if camera == nil then
		return
	end

	if originalFov == nil then
		originalFov = camera.FieldOfView
	end

	camera.FieldOfView = math.clamp(numberFlag("FieldOfView", 70), 40, 120)
end

local function restoreFieldOfView()
	local camera = Workspace.CurrentCamera
	if camera == nil then
		return
	end

	local value = originalFov or defaultFov
	pcall(function()
		camera.FieldOfView = value
	end)
end

-- ==================== GAME HUD ====================

local hiddenGuis = {}

local function setGameHudHidden(hidden)
	local playerGui = player:FindFirstChild("PlayerGui")
	if playerGui == nil then
		return
	end

	local mainGui = playerGui:FindFirstChild("MainGUI")
	if mainGui == nil then
		return
	end

	if hidden then
		if hiddenGuis[mainGui] == nil then
			hiddenGuis[mainGui] = mainGui.Enabled
		end
		mainGui.Enabled = false
		return
	end

	for instance, wasEnabled in pairs(hiddenGuis) do
		pcall(function()
			instance.Enabled = wasEnabled
		end)
	end
	table.clear(hiddenGuis)
end

-- ==================== TARGET HIGHLIGHT ====================

local targetHighlight = nil

local function clearHighlight()
	if targetHighlight == nil then
		return
	end

	local highlight = targetHighlight
	targetHighlight = nil
	pcall(function()
		highlight:Destroy()
	end)
end

local function highlightEgg(part)
	if not isOn("HighlightTarget") then
		clearHighlight()
		return
	end

	if targetHighlight ~= nil and targetHighlight.Parent == part then
		return
	end

	clearHighlight()

	local highlight = Instance.new("Highlight")
	highlight.Name = "SnowHubTarget"
	highlight.FillColor = Color3.fromRGB(255, 196, 92)
	highlight.FillTransparency = 0.65
	highlight.OutlineColor = Color3.fromRGB(255, 232, 176)
	highlight.Parent = part
	targetHighlight = highlight
end

-- ==================== REQUEST BUDGET ====================

local requestTimes = {}

local function pruneRequests()
	local now = os.clock()
	for index = #requestTimes, 1, -1 do
		if now - requestTimes[index] > 60 then
			table.remove(requestTimes, index)
		end
	end
end

local function requestsInLastSecond()
	local now = os.clock()
	local count = 0
	for _, stamp in ipairs(requestTimes) do
		if now - stamp <= 1 then
			count += 1
		end
	end
	return count
end

local function requestsPerMinute()
	pruneRequests()
	return #requestTimes
end

local function requestCap()
	if isOn("SafeMode") then
		return math.clamp(numberFlag("MaxRequests", 3), 1, 5)
	end
	return 10
end

local function consumeBudget()
	if requestsInLastSecond() >= requestCap() then
		return false
	end

	table.insert(requestTimes, os.clock())
	return true
end

local function backoffDelay(failures)
	return math.min(8, 0.5 * (2 ^ math.max(0, failures - 1)))
end

-- ==================== EGGS ====================

local eggs = {}

local function eggKind(part)
	local model = part.Parent
	if model == nil then
		return nil
	end

	if part.Name == "Gold" then
		if string.find(model.Name, "MergeEgg", 1, true) then
			return "Gold egg"
		end
		return nil
	end

	if part.Name == "Egg" then
		return "Normal egg"
	end

	-- verified live: nest parts (p1/p2 MeshParts inside *Nest* models)
	if string.find(model.Name, "Nest", 1, true) ~= nil then
		if string.find(model.Name, "Gold", 1, true) ~= nil then
			return "Gold egg"
		end
		return "Normal egg"
	end

	return nil
end

local function plotOwner(plot)
	for _, attribute in ipairs({ "Owner", "OwnerName", "PlayerName", "OwnerId" }) do
		local value = plot:GetAttribute(attribute)
		if value ~= nil then
			return tostring(value)
		end
	end

	for _, name in ipairs({ "Owner", "OwnerName", "Player" }) do
		local holder = plot:FindFirstChild(name)
		if holder ~= nil then
			if holder:IsA("ObjectValue") and holder.Value ~= nil then
				return holder.Value.Name
			end
			if holder:IsA("StringValue") or holder:IsA("IntValue") then
				return tostring(holder.Value)
			end
		end
	end

	return nil
end

local scanZoneEggs

local function scanEggs()
	eggs = {}

	local plots = Workspace:FindFirstChild("Plots")
	if plots == nil then
		return 0
	end

	for _, plot in ipairs(plots:GetChildren()) do
		local owner = plotOwner(plot)
		for _, descendant in ipairs(plot:GetDescendants()) do
			if not descendant:IsA("BasePart") then
				continue
			end

			local kind = eggKind(descendant)
			if kind == nil then
				continue
			end

			table.insert(eggs, {
				part  = descendant,
				kind  = kind,
				plot  = plot.Name,
				owner = owner,
			})
		end
	end

	scanZoneEggs()

	return #eggs
end

-- verified live: eggs live under Workspace.Build.ZoneBuilds.<Zone>.Eggs
-- as *Nest* models with p1/p2 MeshParts (not under Workspace.Plots).
scanZoneEggs = function()
	local builds = Workspace:FindFirstChild("Build")
	if builds == nil then
		return
	end

	local zones = builds:FindFirstChild("ZoneBuilds")
	if zones == nil then
		return
	end

	for _, zone in ipairs(zones:GetChildren()) do
		local roots = {}
		local eggFolder = zone:FindFirstChild("Eggs")
		if eggFolder ~= nil then
			roots = { eggFolder }
		else
			roots = { zone }
		end

		for _, root in ipairs(roots) do
			for _, descendant in ipairs(root:GetDescendants()) do
				if not descendant:IsA("BasePart") then
					continue
				end

				local kind = eggKind(descendant)
				if kind == nil then
					continue
				end

				table.insert(eggs, {
					part  = descendant,
					kind  = kind,
					plot  = zone.Name,
					owner = nil,
				})
			end
		end
	end
end

local function countGoldEggs()
	local count = 0
	for _, egg in ipairs(eggs) do
		if egg.kind == "Gold egg" and egg.part.Parent ~= nil then
			count = count + 1
		end
	end
	return count
end

local function distanceTo(part)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root == nil then
		return math.huge
	end
	return (part.Position - root.Position).Magnitude
end

local function pickEgg()
	local scope = stringFlag("EggScope", "All plots")
	local filter = stringFlag("EggFilter", "Any egg")
	local limit = numberFlag("MaxDistance", 2500)
	local mine = stringFlag("MyPlot")

	local best = nil
	local bestDistance = math.huge

	for _, egg in ipairs(eggs) do
		local part = egg.part
		if part.Parent == nil then
			continue
		end

		if filter ~= "Any egg" and egg.kind ~= filter then
			continue
		end

		local allowed = true
		if scope == "My plot only" then
			allowed = mine ~= "" and egg.plot == mine
		elseif scope == "Other plots only" then
			allowed = mine ~= "" and egg.plot ~= mine
		end

		if not allowed then
			continue
		end

		local distance = distanceTo(part)
		if distance <= limit and distance < bestDistance then
			best = egg
			bestDistance = distance
		end
	end

	return best, bestDistance
end

-- ==================== REMOTE DISCOVERY ====================

local candidates = {}
local candidateByPath = {}

local RANK_WORDS = {
	"egg", "merge", "break", "steal", "cash", "click", "collect",
	"claim", "open", "sell", "buy", "roll", "upgrade", "speed",
}

local NOISE_WORDS = {
	"analytics", "localization", "leaderboard", "integrity",
	"teleport", "camera", "safety", "policy", "notification",
}

local function fullPath(instance)
	local parts = {}
	local node = instance

	while node ~= nil and node ~= game do
		table.insert(parts, 1, node.Name)
		node = node.Parent
	end

	return table.concat(parts, ".")
end

local function rankRemote(instance)
	local lower = string.lower(instance.Name)
	local score = 0

	for _, word in ipairs(RANK_WORDS) do
		if string.find(lower, word, 1, true) then
			score += 10
		end
	end

	for _, word in ipairs(NOISE_WORDS) do
		if string.find(lower, word, 1, true) then
			score -= 25
		end
	end

	return score
end

local function scanRemotes()
	candidates = {}
	candidateByPath = {}

	local valueCount = 0

	local function visit(root)
		for _, descendant in ipairs(root:GetDescendants()) do
			if descendant:IsA("RemoteEvent") or descendant:IsA("RemoteFunction") then
				local entry = {
					instance  = descendant,
					className = descendant.ClassName,
					name      = descendant.Name,
					path      = fullPath(descendant),
					rank      = rankRemote(descendant),
				}
				table.insert(candidates, entry)
				candidateByPath[entry.path] = entry
			elseif descendant:IsA("ValueBase") then
				valueCount += 1
			end
		end
	end

	visit(game:GetService("ReplicatedStorage"))
	visit(Workspace)
	visit(player)

	table.sort(candidates, function(a, b)
		if a.rank == b.rank then
			return a.name < b.name
		end
		return a.rank > b.rank
	end)

	return { remotes = #candidates, values = valueCount }
end

local discovery = { remotes = 0, values = 0, eggs = 0 }

local function refreshDiscovery()
	local counts = scanRemotes()
	discovery = {
		remotes = counts.remotes,
		values  = counts.values,
		eggs    = scanEggs(),
	}
end

local breakRemoteCache = { name = nil, instance = nil }

local function resolveBreakRemote()
	local name = stringFlag("BreakRemoteName")
	if name == "" then
		return nil
	end

	local cached = breakRemoteCache.instance
	if breakRemoteCache.name == name and cached ~= nil and cached.Parent ~= nil then
		return cached
	end

	local found = nil
	for _, descendant in ipairs(game:GetService("ReplicatedStorage"):GetDescendants()) do
		if descendant.Name == name and (descendant:IsA("RemoteEvent") or descendant:IsA("RemoteFunction")) then
			found = descendant
			break
		end
	end

	if found == nil then
		for _, descendant in ipairs(Workspace:GetDescendants()) do
			if descendant.Name == name and (descendant:IsA("RemoteEvent") or descendant:IsA("RemoteFunction")) then
				found = descendant
				break
			end
		end
	end

	breakRemoteCache.name = name
	breakRemoteCache.instance = found
	return found
end

local function testCandidate(path)
	local candidate = candidateByPath[path]
	if candidate == nil then
		return "Not in the current scan"
	end

	local instance = candidate.instance
	if instance == nil or instance.Parent == nil then
		return "Instance is gone: " .. path
	end

	if not isOn("AllowRemoteTest") then
		return string.format("%s readable, firing disabled", candidate.className)
	end

	if not consumeBudget() then
		return "Request budget full, wait a second"
	end

	if instance:IsA("RemoteFunction") then
		local ok, result = pcall(function()
			return instance:InvokeServer()
		end)
		if ok then
			return "ok: " .. tostring(result)
		end
		return "fail: " .. tostring(result)
	end

	local ok, err = pcall(function()
		instance:FireServer()
	end)
	if ok then
		return "ok: fired with no arguments"
	end
	return "fail: " .. tostring(err)
end

-- ==================== ACTIONS ====================

local function findClickDetector(part)
	local detector = part:FindFirstChildOfClass("ClickDetector")
	if detector ~= nil then
		return detector
	end

	local model = part.Parent
	if model ~= nil then
		detector = model:FindFirstChildOfClass("ClickDetector")
		if detector ~= nil then
			return detector
		end
	end

	return nil
end

-- verified live: MasteryPickaxeSwing() + EggHitRequest(part) raises Cash
-- (+81k per hit in testing) and yields EggHitLanded. This is the primary
-- break path; click/prompt/configured remotes below are fallbacks.
local function verifiedHit(part)
	local rs = game:GetService("ReplicatedStorage")
	local req = rs:FindFirstChild("EggHitRequest")
	if req == nil or not req:IsA("RemoteEvent") then
		return false, "no EggHitRequest"
	end

	if not consumeBudget() then
		return false, "request budget full"
	end

	local swing = rs:FindFirstChild("MasteryPickaxeSwing")
	if swing ~= nil and swing:IsA("RemoteEvent") then
		if consumeBudget() then
			pcall(function()
				swing:FireServer()
			end)
		end
		task.wait(0.35)
	end

	local ok = pcall(function()
		req:FireServer(part)
	end)
	return ok, ok and "egg hit" or "egg hit failed"
end

local function breakEgg(egg)
	local part = egg.part
	if part == nil or part.Parent == nil then
		return false, "egg gone"
	end

	local hitOk, hitReason = verifiedHit(part)
	if hitOk then
		return true, hitReason
	end
	if hitReason == "request budget full" then
		return false, hitReason
	end

	if not consumeBudget() then
		return false, "request budget full"
	end

	local detector = findClickDetector(part)
	if detector ~= nil and type(fireclickdetector) == "function" then
		local ok = pcall(fireclickdetector, detector, 1)
		return ok, ok and "click detector" or "click detector failed"
	end

	local prompt = part:FindFirstChildOfClass("ProximityPrompt")
	if prompt == nil and part.Parent ~= nil then
		prompt = part.Parent:FindFirstChildOfClass("ProximityPrompt")
	end
	if prompt ~= nil and type(fireproximityprompt) == "function" then
		local ok = pcall(fireproximityprompt, prompt, 1)
		return ok, ok and "proximity prompt" or "proximity prompt failed"
	end

	local remote = resolveBreakRemote()
	if remote ~= nil then
		local ok = pcall(function()
			if remote:IsA("RemoteFunction") then
				remote:InvokeServer(part)
			else
				remote:FireServer(part)
			end
		end)
		return ok, ok and "configured remote" or "remote failed"
	end

	return false, "no break handler"
end

local function approachEgg(egg)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if root == nil or humanoid == nil then
		return false
	end

	local deadline = os.clock() + 8
	while os.clock() < deadline and alive do
		local part = egg.part
		if part == nil or part.Parent == nil then
			return false
		end

		local offset = part.Position - root.Position
		if Vector3.new(offset.X, 0, offset.Z).Magnitude <= 7 then
			return true
		end

		humanoid:MoveTo(part.Position)
		task.wait(0.12 + math.random() * 0.08)
	end

	return false
end

local lastTeleport = 0

local function teleportToPlot()
	local now = os.clock()
	if now - lastTeleport < 3 then
		return false, "teleport cooling down"
	end

	local plotName = stringFlag("MyPlot")
	if plotName == "" then
		return false, "set a plot name first"
	end

	local plots = Workspace:FindFirstChild("Plots")
	local plot = plots and plots:FindFirstChild(plotName)
	if plot == nil then
		return false, "plot not found"
	end

	local spawnPoint = plot:FindFirstChild("SpawnPoint", true)
	if spawnPoint == nil then
		return false, "plot has no SpawnPoint"
	end

	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if root == nil or humanoid == nil then
		return false, "no character"
	end

	lastTeleport = now
	local ok = pcall(function()
		root.CFrame = CFrame.new(spawnPoint.Position + Vector3.new(0, 3, 0))
	end)

	if ok then
		return true, "moved to " .. plotName
	end
	return false, "teleport failed"
end

local function teleportToEgg(egg)
	local now = os.clock()
	if now - lastTeleport < 3 then
		return false, "teleport cooling down"
	end

	local part = egg.part
	if part == nil or part.Parent == nil then
		return false, "egg gone"
	end

	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if root == nil or humanoid == nil then
		return false, "no character"
	end

	if humanoid.MoveDirection.Magnitude > 0.1 then
		return false, "moving"
	end

	lastTeleport = now
	local ok = pcall(function()
		root.CFrame = CFrame.new(part.Position + Vector3.new(0, 4, 6))
	end)

	if ok then
		task.wait(0.6)
		return true, "moved to egg"
	end
	return false, "teleport failed"
end

-- eggs can be thousands of studs away: teleport when far, walk when near.
local function travelToEgg(egg, distance)
	if distance <= 7 then
		return true, "in range"
	end

	if distance > 60 then
		return teleportToEgg(egg)
	end

	if approachEgg(egg) then
		return true, "walked to egg"
	end
	return false, "could not reach egg"
end

-- ==================== UI BUILD ====================

local win = Library:Window({
	Title     = "Snowy Studios",
	Subtitle  = GAME_NAME,
	Logo      = "rbxassetid://123802801726537",
	IconPack  = "phosphor",
	Keybind   = Enum.KeyCode.RightControl,
	Width     = 720,
	Height    = 600,
	MinHeight = 340,
	MaxHeight = 700,
})

activeRawWin = win

local uiErrors = 0

local TAB_ICONS = {
	Main            = "house",
	Player          = "user",
	Info            = "info",
	Diagnostics     = "wrench",
	["UI Settings"] = "gear",
}

local function tab(name)
	local ok, result = pcall(function()
		return win:Tab({ Name = name, Icon = TAB_ICONS[name] })
	end)
	if not ok or result == nil then
		uiErrors += 1
	end
	return result
end

local function section(tabHandle, title, column)
	local ok, result = pcall(function()
		return tabHandle:Section({ Title = title, Column = column })
	end)
	if not ok or result == nil then
		uiErrors += 1
	end
	return result
end

local function add(sectionHandle, kind, options)
	if sectionHandle == nil then
		uiErrors += 1
		return nil
	end

	local method = sectionHandle[kind]
	if type(method) ~= "function" then
		uiErrors += 1
		return nil
	end

	local ok, result = pcall(method, sectionHandle, options)
	if not ok then
		uiErrors += 1
		return nil
	end

	return result
end

local function makeLabel(sectionHandle, text)
	local handle = add(sectionHandle, "Label", text)
	if handle == nil then
		handle = add(sectionHandle, "Label", { Text = text })
	end
	return handle
end

local refreshDiagnostics

local mainTab = tab("Main")
local playerTab = tab("Player")
local infoTab = tab("Info")
local diagTab = tab("Diagnostics")
local settingsTab = tab("UI Settings")

-- ---------- Main / Farm ----------

local farmSection = section(mainTab, "Farm", 1)
local farmStatus = makeLabel(farmSection, "Idle")

add(farmSection, "Toggle", {
	Text     = "Auto farm eggs",
	Default  = false,
	Flag     = "AutoFarmEggs",
	Callback = function(state)
		mirror.AutoFarmEggs = state
		setLabel(farmStatus, state and "Looking for eggs" or "Idle")
	end,
})

add(farmSection, "Slider", {
	Text     = "Break delay",
	Min      = 0.15,
	Max      = 2,
	Default  = 0.45,
	Decimals = 2,
	Flag     = "BreakDelay",
	Callback = function(value)
		mirror.BreakDelay = tonumber(value) or 0.45
	end,
})

add(farmSection, "Dropdown", {
	Text     = "Egg filter",
	Options  = { "Any egg", "Normal egg", "Gold egg" },
	Flag     = "EggFilter",
	Callback = function(value)
		mirror.EggFilter = value
	end,
})

-- ---------- Main / Targeting ----------

local targetSection = section(mainTab, "Targeting", 2)
local targetStatus = makeLabel(targetSection, "Scanning plots")

add(targetSection, "Dropdown", {
	Text     = "Scope",
	Options  = { "All plots", "Other plots only", "My plot only" },
	Flag     = "EggScope",
	Callback = function(value)
		mirror.EggScope = value
	end,
})

add(targetSection, "Slider", {
	Text     = "Max distance",
	Min      = 20,
	Max      = 5000,
	Default  = 2500,
	Decimals = 0,
	Flag     = "MaxDistance",
	Callback = function(value)
		mirror.MaxDistance = tonumber(value) or 2500
	end,
})

add(targetSection, "Toggle", {
	Text     = "Walk to egg",
	Default  = true,
	Flag     = "ApproachEggs",
	Callback = function(state)
		mirror.ApproachEggs = state
	end,
})

add(targetSection, "Toggle", {
	Text     = "Highlight target",
	Default  = false,
	Flag     = "HighlightTarget",
	Callback = function(state)
		mirror.HighlightTarget = state
		if not state then
			clearHighlight()
		end
	end,
})

-- ---------- Main / Actions ----------

local actionSection = section(mainTab, "Actions", 1)
local actionStatus = makeLabel(actionSection, "Ready")

add(actionSection, "Button", {
	Text       = "Break nearest egg",
	ButtonText = "Run",
	Callback   = function()
		if not allowPress("breakNow") then
			return
		end

		local egg, distance = pickEgg()
		if egg == nil then
			setLabel(actionStatus, "No egg in range")
			return
		end

		if isOn("ApproachEggs") and distance > 7 then
			local reached, travelReason = travelToEgg(egg, distance)
			if not reached then
				setLabel(actionStatus, "Travel: " .. travelReason)
				return
			end
		end

		local ok, reason = breakEgg(egg)
		if ok then
			setLabel(actionStatus, "Broke " .. egg.kind .. " on " .. egg.plot .. " via " .. reason)
		else
			setLabel(actionStatus, "Failed: " .. reason)
		end
	end,
})

add(actionSection, "Button", {
	Text       = "Rescan eggs",
	ButtonText = "Scan",
	Callback   = function()
		if not allowPress("rescanEggs") then
			return
		end

		local count = scanEggs()
		setLabel(actionStatus, string.format("Found %d eggs on plots", count))
	end,
})

-- ---------- Main / Requests ----------

local requestSection = section(mainTab, "Requests", 2)
local rateStatus = makeLabel(requestSection, "0 req/min")

add(requestSection, "Toggle", {
	Text     = "Safe mode",
	Default  = true,
	Flag     = "SafeMode",
	Callback = function(state)
		mirror.SafeMode = state
	end,
})

add(requestSection, "Slider", {
	Text     = "Max requests/sec",
	Min      = 1,
	Max      = 5,
	Default  = 3,
	Decimals = 0,
	Flag     = "MaxRequests",
	Callback = function(value)
		mirror.MaxRequests = tonumber(value) or 3
	end,
})

-- ---------- Player / Movement ----------

local moveSection = section(playerTab, "Movement", 1)
local moveStatus = makeLabel(moveSection, "Game defaults")

add(moveSection, "Toggle", {
	Text     = "Override movement",
	Default  = false,
	Flag     = "OverrideMovement",
	Callback = function(state)
		mirror.OverrideMovement = state
		applyMovement()
		setLabel(moveStatus, state and "Override active" or "Game defaults")
	end,
})

add(moveSection, "Slider", {
	Text     = "Walk speed",
	Min      = 8,
	Max      = 80,
	Default  = 16,
	Decimals = 0,
	Flag     = "WalkSpeed",
	Callback = function(value)
		mirror.WalkSpeed = tonumber(value) or 16
		applyMovement()
	end,
})

add(moveSection, "Slider", {
	Text     = "Jump power",
	Min      = 0,
	Max      = 120,
	Default  = 50,
	Decimals = 0,
	Flag     = "JumpPower",
	Callback = function(value)
		mirror.JumpPower = tonumber(value) or 50
		applyMovement()
	end,
})

add(moveSection, "Button", {
	Text       = "Reset movement",
	ButtonText = "Reset",
	Callback   = function()
		if not allowPress("resetMovement") then
			return
		end

		restoreMovement()
		mirror.OverrideMovement = false
		setLabel(moveStatus, "Game defaults")
	end,
})

-- ---------- Player / Camera ----------

local cameraSection = section(playerTab, "Camera", 2)

add(cameraSection, "Slider", {
	Text     = "Field of view",
	Min      = 40,
	Max      = 120,
	Default  = 70,
	Decimals = 0,
	Flag     = "FieldOfView",
	Callback = function(value)
		mirror.FieldOfView = tonumber(value) or 70
		applyFieldOfView()
	end,
})

-- ---------- Player / Travel ----------

local travelSection = section(playerTab, "Travel", 1)
local travelStatus = makeLabel(travelSection, "Not moved")

add(travelSection, "Input", {
	Text    = "Plot name",
	Flag    = "MyPlot",
	Default = "",
})

add(travelSection, "Button", {
	Text       = "Teleport to plot",
	ButtonText = "Go",
	Callback   = function()
		if not allowPress("teleport", 3) then
			setLabel(travelStatus, "Teleport cooling down")
			return
		end

		local ok, reason = teleportToPlot()
		setLabel(travelStatus, reason)
		if not ok then
			notify(reason, "error", 4)
		end
	end,
})

-- ---------- Info ----------

local stateSection = section(infoTab, "State", 1)
local cashStatus = makeLabel(stateSection, "Cash/s: --")
local speedStatus = makeLabel(stateSection, "Speed: --")
local eggCountStatus = makeLabel(stateSection, "Eggs: --")
local sessionStatus = makeLabel(stateSection, "Session: 0:00:00")

local linkSection = section(infoTab, "Connection", 2)
local placeStatus = makeLabel(linkSection, "Place: " .. tostring(PLACE_ID))
local jobStatus = makeLabel(linkSection, "Job: " .. JOB_ID)
local userStatus = makeLabel(linkSection, "User: " .. tostring(player.UserId))
local remoteStatus = makeLabel(linkSection, "Remotes: --")

add(linkSection, "Button", {
	Text       = "Copy job id",
	ButtonText = "Copy",
	Callback   = function()
		if not allowPress("copyJob") then
			return
		end

		if type(setclipboard) ~= "function" then
			notify("Clipboard unavailable", "error", 4)
			return
		end

		local ok = pcall(setclipboard, JOB_ID)
		notify(ok and "Job id copied" or "Copy failed", ok and "success" or "error", 3)
	end,
})

-- ---------- Diagnostics ----------

local diagSection = section(diagTab, "Discovery", 1)
local diagCounts = makeLabel(diagSection, "Scanning game")
local diagResult = makeLabel(diagSection, "No test run")

local optionToPath = {}

local function buildCandidateList()
	local options = {}
	optionToPath = {}

	for _, candidate in ipairs(candidates) do
		if #options >= 60 then
			break
		end

		local option = string.format("%s | %s | %s", candidate.className, candidate.name, candidate.path)
		table.insert(options, option)
		optionToPath[option] = candidate.path
	end

	if #options == 0 then
		table.insert(options, "none | none | no remotes found")
	end

	return options
end

add(diagSection, "Dropdown", {
	Text     = "Candidate",
	Options  = buildCandidateList(),
	Multi    = false,
	Flag     = "CandidatePath",
	Callback = function(value)
		mirror.CandidatePath = optionToPath[value] or value
	end,
})

add(diagSection, "Button", {
	Text       = "Re-scan",
	ButtonText = "Scan",
	Callback   = function()
		if not allowPress("rescanRemotes") then
			return
		end

		refreshDiscovery()
		refreshDiagnostics()
		setLabel(diagResult, string.format("Scan done: %d remotes", discovery.remotes))
	end,
})

add(diagSection, "Button", {
	Text       = "Test selected",
	ButtonText = "Test",
	Callback   = function()
		if not allowPress("testCandidate") then
			return
		end

		local path = stringFlag("CandidatePath")
		if path == "" then
			setLabel(diagResult, "Select a candidate first")
			return
		end

		setLabel(diagResult, testCandidate(path))
	end,
})

add(diagSection, "Button", {
	Text       = "Copy path",
	ButtonText = "Copy",
	Callback   = function()
		if not allowPress("copyPath") then
			return
		end

		local path = stringFlag("CandidatePath")
		if path == "" then
			setLabel(diagResult, "Select a candidate first")
			return
		end

		if type(setclipboard) ~= "function" then
			setLabel(diagResult, "Clipboard unavailable: " .. path)
			return
		end

		local ok = pcall(setclipboard, path)
		setLabel(diagResult, ok and ("Copied " .. path) or "Copy failed")
	end,
})

local diagSafety = section(diagTab, "Safety", 2)
local boundStatus = makeLabel(diagSafety, "Bindings: scanning")
local unboundStatus = makeLabel(diagSafety, "Unbound: scanning")

add(diagSafety, "Toggle", {
	Text     = "Allow remote test fire",
	Default  = false,
	Flag     = "AllowRemoteTest",
	Callback = function(state)
		mirror.AllowRemoteTest = state
	end,
})

add(diagSafety, "Input", {
	Text    = "Break remote name",
	Flag    = "BreakRemoteName",
	Default = "",
})

local diagNote = makeLabel(
	diagSafety,
	"Click detector and proximity prompt are preferred; a remote is only used when named above."
)

-- ---------- UI Settings ----------

local menuSection = section(settingsTab, "Menu", 1)
local menuStatus = makeLabel(menuSection, "RightControl opens the menu")

add(menuSection, "Keybind", {
	Text      = "Menu keybind",
	Default   = "RightControl",
	Flag      = "MenuKeybind",
	OnChanged = function(key)
		local code = nil
		if typeof(key) == "EnumItem" then
			code = key
		elseif type(key) == "string" then
			local ok, resolved = pcall(function()
				return Enum.KeyCode[key]
			end)
			if ok then
				code = resolved
			end
		end

		if code == nil then
			return
		end

		mirror.MenuKeybind = tostring(code)
		invoke(win, "SetKeybind", code)
		setLabel(menuStatus, tostring(code) .. " opens the menu")
	end,
})

add(menuSection, "Button", {
	Text       = "Unload",
	ButtonText = "Unload",
	Callback   = function()
		if not allowPress("unload") then
			return
		end
		unload()
	end,
})

local interfaceSection = section(settingsTab, "Interface", 2)
local interfaceStatus = makeLabel(interfaceSection, "Default interface")

add(interfaceSection, "Toggle", {
	Text     = "Notifications",
	Default  = true,
	Flag     = "Notifications",
	Callback = function(state)
		mirror.Notifications = state
	end,
})

add(interfaceSection, "Toggle", {
	Text     = "Hide game HUD",
	Default  = false,
	Flag     = "HideGameHud",
	Callback = function(state)
		mirror.HideGameHud = state
		setGameHudHidden(state)
		setLabel(interfaceStatus, state and "Game HUD hidden" or "Game HUD visible")
	end,
})

-- ==================== DIAGNOSTICS REFRESH ====================

refreshDiagnostics = function()
	local withDetector = 0
	local withPrompt = 0

	for _, egg in ipairs(eggs) do
		local part = egg.part
		if part.Parent ~= nil then
			if findClickDetector(part) ~= nil then
				withDetector += 1
			elseif part:FindFirstChildOfClass("ProximityPrompt") ~= nil then
				withPrompt += 1
			end
		end
	end

	local bound = 0
	local unbound = {}

	if type(fireclickdetector) == "function" and withDetector > 0 then
		bound += 1
	else
		table.insert(unbound, "click detector break")
	end

	if type(fireproximityprompt) == "function" and withPrompt > 0 then
		bound += 1
	else
		table.insert(unbound, "proximity prompt break")
	end

	if resolveBreakRemote() ~= nil then
		bound += 1
	else
		table.insert(unbound, "named break remote")
	end

	local hitRemote = game:GetService("ReplicatedStorage"):FindFirstChild("EggHitRequest")
	if hitRemote ~= nil and hitRemote:IsA("RemoteEvent") then
		bound += 1
	else
		table.insert(unbound, "egg hit (EggHitRequest)")
	end

	local plotName = stringFlag("MyPlot")
	local plots = Workspace:FindFirstChild("Plots")
	if plotName ~= "" and plots ~= nil and plots:FindFirstChild(plotName) ~= nil then
		bound += 1
	else
		table.insert(unbound, "plot teleport")
	end

	setLabel(boundStatus, string.format("Bindings: %d bound", bound))
	setLabel(diagCounts, string.format(
		"Remotes: %d | Values: %d | Eggs: %d | Bound: %d",
		discovery.remotes,
		discovery.values,
		discovery.eggs,
		bound
	))

	if #unbound == 0 then
		setLabel(unboundStatus, "Unbound: none")
	else
		setLabel(unboundStatus, "Unbound: " .. table.concat(unbound, ", "))
	end
end

-- ==================== LOOPS ====================

task.spawn(function()
	local gen = generation
	local failures = 0

	while isCurrentInstance(gen) do
		if not isOn("AutoFarmEggs") then
			failures = 0
			task.wait(0.2)
			continue
		end

		local egg, distance = pickEgg()
		if egg == nil then
			setLabel(farmStatus, "No eggs in range")
			clearHighlight()
			task.wait(1)
			continue
		end

		highlightEgg(egg.part)

		if isOn("ApproachEggs") and distance > 7 then
			local reached, travelReason = travelToEgg(egg, distance)
			if not reached then
				setLabel(farmStatus, "Travel: " .. travelReason)
				task.wait(0.5)
				continue
			end
		end

		local ok, reason = breakEgg(egg)

		if ok then
			failures = 0
			setLabel(farmStatus, string.format("Broke %s on %s via %s", egg.kind, egg.plot, reason))
		elseif reason == "request budget full" then
			setLabel(farmStatus, "Throttled by request budget")
			task.wait(0.4)
			continue
		else
			failures += 1
			setLabel(farmStatus, "Failed: " .. reason)

			if failures >= 5 then
				forceOff("AutoFarmEggs")
				clearHighlight()
				notify("Auto farm disabled after repeated failures: " .. reason, "error", 6)
				failures = 0
				task.wait(1)
				continue
			end

			task.wait(backoffDelay(failures))
			continue
		end

		task.wait(numberFlag("BreakDelay", 0.45) + math.random() * 0.1)
	end
end)

task.spawn(function()
	local gen = generation
	local tick = 0

	while isCurrentInstance(gen) do
		setLabel(cashStatus, "Cash/s: " .. readLeaderstat("Cash/s"))
		setLabel(speedStatus, "Speed: " .. readLeaderstat("Speed"))
		setLabel(eggCountStatus, string.format("Eggs: %d on plots (%d gold)", #eggs, countGoldEggs()))
		setLabel(sessionStatus, "Session: " .. formatDuration(os.clock() - startedAt))
		setLabel(placeStatus, "Place: " .. tostring(PLACE_ID) .. " | " .. GAME_NAME)
		setLabel(jobStatus, "Job: " .. JOB_ID)
		setLabel(userStatus, "User: " .. tostring(player.UserId) .. " | " .. tostring(#Players:GetPlayers()) .. " in server")
		setLabel(remoteStatus, string.format("Remotes: %d | Values: %d", discovery.remotes, discovery.values))
		setLabel(rateStatus, string.format("%d req/min | cap %d/s", requestsPerMinute(), requestCap()))

		local _, nearest = pickEgg()
		if nearest ~= math.huge then
			setLabel(targetStatus, string.format("%d eggs, nearest %d studs", #eggs, math.floor(nearest)))
		else
			setLabel(targetStatus, string.format("%d eggs in range", #eggs))
		end

		tick += 1
		if tick % 5 == 0 then
			scanEggs()
		end
		if tick % 15 == 0 then
			refreshDiagnostics()
		end

		task.wait(1)
	end
end)

-- ==================== CHARACTER ====================

track(player.CharacterAdded:Connect(function(character)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if humanoid == nil then
		return
	end

	if isOn("OverrideMovement") then
		humanoid.WalkSpeed = math.clamp(numberFlag("WalkSpeed", 16), 8, 80)
		humanoid.JumpPower = math.clamp(numberFlag("JumpPower", 50), 0, 120)
	end
end))

-- ==================== UNLOAD ====================

unload = function()
	if not alive then
		return
	end

	alive = false
	generation += 1

	clearHighlight()
	restoreMovement()
	restoreFieldOfView()
	setGameHudHidden(false)

	for _, connection in ipairs(connections) do
		pcall(function()
			connection:Disconnect()
		end)
	end
	table.clear(connections)

	invoke(Library, "Unload")

	if getgenv().SnowyStudiosUnload == unload then
		getgenv().SnowyStudiosUnload = nil
	end

	print("[Snow Hub] unloaded")
end

getgenv().SnowyStudiosUnload = unload

-- ==================== START ====================

invoke(win, "SetFooter", string.format("v1.4 | %s | %d", GAME_NAME, player.UserId))

refreshDiagnostics()
setLabel(menuStatus, string.format("%s opens the menu", stringFlag("MenuKeybind", "RightControl")))

if uiErrors > 0 then
	notify(string.format("Library built with %d guard fallbacks; check Diagnostics", uiErrors), "error", 6)
end

-- keep the panel on top and visible for whoever runs the script.
pcall(function()
	local holder = (gethui and gethui()) or game:GetService("CoreGui")
	for _, gui in ipairs(holder:GetChildren()) do
		if gui:IsA("ScreenGui") then
			for _, descendant in ipairs(gui:GetDescendants()) do
				if (descendant:IsA("TextLabel") or descendant:IsA("TextButton")) and descendant.Text == "Snowy Studios" then
					gui.DisplayOrder = 999
					gui.Enabled = true
					break
				end
			end
		end
	end
end)

notify("Auto farm ready. Press Auto farm eggs to start.", "success", 6)
print(GAME_NAME .. " loaded")