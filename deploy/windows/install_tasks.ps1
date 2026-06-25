$ErrorActionPreference = "Stop"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$HttpScript = Join-Path $AppDir "deploy\windows\run_http.ps1"
$HttpsScript = Join-Path $AppDir "deploy\windows\run_https.ps1"

function Register-NutritionTask {
    param(
        [Parameter(Mandatory = $true)][string]$TaskName,
        [Parameter(Mandatory = $true)][string]$ScriptPath
    )

    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Days 365) `
        -RestartCount 999 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Runs NutritionApp from $AppDir" `
        -Force | Out-Null
}

Register-NutritionTask -TaskName "NutritionApp HTTP" -ScriptPath $HttpScript
Register-NutritionTask -TaskName "NutritionApp HTTPS" -ScriptPath $HttpsScript

Start-ScheduledTask -TaskName "NutritionApp HTTP"
if (Test-Path (Join-Path $AppDir "certs\fullchain.pem")) {
    Start-ScheduledTask -TaskName "NutritionApp HTTPS"
}

Write-Host "Registered NutritionApp scheduled tasks."
