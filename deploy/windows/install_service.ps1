# Installs NutritionApp as an always-on background server on Windows.
#
# Unlike install_tasks.ps1 / install_startup_shortcut.ps1 (which only start the
# app AFTER an interactive logon), this registers a scheduled task that:
#   - starts at system boot, with NO user logged in
#   - keeps running after you log out
#   - runs as your user via S4U ("run whether user is logged on or not"),
#     so the per-user Python venv keeps working, and WITHOUT storing a password
#   - is kept alive by run_watchdog.ps1 (HTTP + HTTPS) and auto-restarts on crash
# It also disables sleep/hibernate while on AC power so the server stays reachable.
#
# Run this in an ELEVATED PowerShell (Run as Administrator).

param([switch]$Pause)

$ErrorActionPreference = "Stop"

# --- self-elevate (needed for S4U principal, RunLevel Highest, powercfg) ---
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Administrator rights required - relaunching elevated (approve the UAC prompt)..."
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"", "-Pause")
    return
}

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$WatchdogScript = Join-Path $AppDir "deploy\windows\run_watchdog.ps1"
$DuckDnsScript  = Join-Path $AppDir "deploy\windows\run_duckdns_updater.ps1"
$User = "$env:USERDOMAIN\$env:USERNAME"

Write-Host "App dir : $AppDir"
Write-Host "Run as  : $User (S4U, run whether logged on or not)"

# --- remove the old logon-only mechanisms so we don't end up with duplicates ---
foreach ($legacy in @("NutritionApp HTTP", "NutritionApp HTTPS")) {
    if (Get-ScheduledTask -TaskName $legacy -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $legacy -Confirm:$false
        Write-Host "Removed legacy logon task: $legacy"
    }
}
$StartupDir = [Environment]::GetFolderPath("Startup")
foreach ($lnk in @("NutritionApp Server.lnk", "NutritionApp DuckDNS.lnk")) {
    $p = Join-Path $StartupDir $lnk
    if (Test-Path $p) { Remove-Item $p -Force; Write-Host "Removed legacy startup shortcut: $lnk" }
}

# --- common task pieces ---
$principal = New-ScheduledTaskPrincipal -UserId $User -LogonType S4U -RunLevel Highest
$trigger   = New-ScheduledTaskTrigger -AtStartup
$settings  = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

function Register-NutritionTask {
    param([string]$TaskName, [string]$ScriptPath)
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings `
        -Description "Always-on NutritionApp from $AppDir" -Force | Out-Null
    Write-Host "Registered task: $TaskName"
}

# main server (watchdog keeps HTTP + HTTPS up)
Register-NutritionTask -TaskName "NutritionApp" -ScriptPath $WatchdogScript

# optional DuckDNS updater
if (Test-Path (Join-Path $AppDir ".duckdns.env")) {
    Register-NutritionTask -TaskName "NutritionApp DuckDNS" -ScriptPath $DuckDnsScript
}

# --- keep the machine awake on AC so it can serve requests (monitor may sleep) ---
powercfg /change standby-timeout-ac 0   | Out-Null
powercfg /change hibernate-timeout-ac 0 | Out-Null
Write-Host "Disabled sleep/hibernate on AC power (screen timeout left unchanged)."

# --- start now (won't double-bind: the watchdog skips ports already listening) ---
Start-ScheduledTask -TaskName "NutritionApp"
if (Get-ScheduledTask -TaskName "NutritionApp DuckDNS" -ErrorAction SilentlyContinue) {
    Start-ScheduledTask -TaskName "NutritionApp DuckDNS"
}

Write-Host ""
Write-Host "Done. NutritionApp will now start at boot (no login needed) and survive logout."
Write-Host "Logs: $AppDir\logs\nutrition-watchdog.log"

if ($Pause) { Read-Host "`nPress Enter to close" }
