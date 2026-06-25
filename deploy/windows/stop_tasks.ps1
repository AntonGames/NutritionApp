$ErrorActionPreference = "SilentlyContinue"

# Stop and remove every NutritionApp auto-start mechanism:
#   - new always-on task (install_service.ps1): "NutritionApp", "NutritionApp DuckDNS"
#   - legacy logon tasks (install_tasks.ps1): "NutritionApp HTTP", "NutritionApp HTTPS"
foreach ($taskName in @("NutritionApp", "NutritionApp DuckDNS", "NutritionApp HTTP", "NutritionApp HTTPS")) {
    Stop-ScheduledTask -TaskName $taskName
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# legacy startup-folder shortcuts (install_startup_shortcut.ps1)
$StartupDir = [Environment]::GetFolderPath("Startup")
foreach ($lnk in @("NutritionApp Server.lnk", "NutritionApp DuckDNS.lnk")) {
    Remove-Item (Join-Path $StartupDir $lnk) -Force
}

# kill running watchdog + uvicorn workers
Get-Process python | Where-Object {
    $_.Path -like "*\NutritionApp\.venv\Scripts\python.exe"
} | Stop-Process -Force

Write-Host "Stopped NutritionApp tasks, removed auto-start entries, and killed local Python workers."
