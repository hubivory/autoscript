param(
    [Parameter(Mandatory = $true)][string]$Bridge,
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$PlaceId = "114326934417838",
    [string]$Adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
    [string]$AutoexecDir = "/sdcard/Delta/Autoexecute",
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Adb)) {
    throw "adb not found at $Adb"
}

$device = (& $Adb get-state) 2>$null
if ($device -ne "device") {
    throw "no adb device in 'device' state (got '$device')"
}

$Bridge = $Bridge.TrimEnd("/")
$script = @(
    "getgenv().MCP_AUTH_TOKEN = `"$Token`"",
    "getgenv().BridgeURL = `"$Bridge`"",
    "loadstring(game:HttpGet(`"$Bridge/mobile-connector.luau`"))(`"$Bridge`")"
) -join "`n"

$tmp = Join-Path $env:TEMP "mcp_connect.txt"
[IO.File]::WriteAllText($tmp, $script + "`n", [Text.Encoding]::ASCII)

& $Adb push $tmp "$AutoexecDir/mcp_connect.txt" | Out-Null
Write-Host "pushed $AutoexecDir/mcp_connect.txt"

if (-not $NoLaunch) {
    & $Adb shell am force-stop com.roblox.client | Out-Null
    Start-Sleep -Seconds 2
    & $Adb shell am start -a android.intent.action.VIEW -d "roblox://placeId=$PlaceId" | Out-Null
    Write-Host "launched roblox://placeId=$PlaceId"
}
