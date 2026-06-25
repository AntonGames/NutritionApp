$ErrorActionPreference = "Stop"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WatchdogScript = Join-Path $AppDir "deploy\windows\run_watchdog.ps1"
$DuckDnsScript = Join-Path $AppDir "deploy\windows\run_duckdns_updater.ps1"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "NutritionApp Server.lnk"
$DuckDnsShortcutPath = Join-Path $StartupDir "NutritionApp DuckDNS.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WatchdogScript`""
$shortcut.WorkingDirectory = $AppDir
$shortcut.WindowStyle = 7
$shortcut.Description = "Starts and monitors NutritionApp local server"
$shortcut.Save()

$duckDnsShortcut = $shell.CreateShortcut($DuckDnsShortcutPath)
$duckDnsShortcut.TargetPath = "powershell.exe"
$duckDnsShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$DuckDnsScript`""
$duckDnsShortcut.WorkingDirectory = $AppDir
$duckDnsShortcut.WindowStyle = 7
$duckDnsShortcut.Description = "Updates DuckDNS for NutritionApp"
$duckDnsShortcut.Save()

Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$WatchdogScript`""
)

if (Test-Path (Join-Path $AppDir ".duckdns.env")) {
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$DuckDnsScript`""
    )
}

Write-Host "Installed startup shortcut: $ShortcutPath"
Write-Host "Installed startup shortcut: $DuckDnsShortcutPath"
