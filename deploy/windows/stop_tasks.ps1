$ErrorActionPreference = "SilentlyContinue"

foreach ($taskName in @("NutritionApp HTTP", "NutritionApp HTTPS")) {
    Stop-ScheduledTask -TaskName $taskName
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Get-Process python | Where-Object {
    $_.Path -like "*\NutritionApp\.venv\Scripts\python.exe"
} | Stop-Process -Force

Write-Host "Stopped NutritionApp scheduled tasks and local Python workers."
