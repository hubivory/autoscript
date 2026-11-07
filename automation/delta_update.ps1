param(
    [string]$Adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
    [string]$OutDir = "$env:TEMP\delta_update"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Adb)) {
    throw "adb not found at $Adb"
}

$state = (& $Adb get-state) 2>$null
if ($state -ne "device") {
    throw "no adb device in 'device' state (got '$state')"
}

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$api = Invoke-RestMethod -Uri "https://delta.filenetwork.vip/get_files.php" -TimeoutSec 60
$latest = $api.latest_apk | Select-Object -First 1
if (-not $latest -or -not $latest.name) {
    throw "no latest_apk entry in file list"
}

$name = [string]$latest.name
$size = [long]$latest.size
Write-Host "latest: $name ($size bytes)"

$apk = Join-Path $OutDir $name
$have = (Test-Path $apk) -and ((Get-Item $apk).Length -eq $size)
if (-not $have) {
    Write-Host "downloading https://delta.filenetwork.vip/file/$name"
    & curl.exe -L --fail -o $apk "https://delta.filenetwork.vip/file/$name"
}
$actual = (Get-Item $apk).Length
if ($actual -ne $size) {
    throw "size mismatch: expected $size, got $actual"
}
Write-Host "verified $apk ($actual bytes)"

Write-Host "installing (preserving app data)..."
$install = & $Adb install -r $apk 2>&1
$install | Out-String | Write-Host
if ($install -notmatch "Success") {
    throw "adb install failed: $install"
}

$ver = (& $Adb shell dumpsys package com.roblox.client) 2>$null | Select-String "versionName" | Select-Object -First 1
Write-Host "installed: $ver"
