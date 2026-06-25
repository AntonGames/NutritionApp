$ErrorActionPreference = "Stop"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LogDir = Join-Path $AppDir "logs"
$HttpScript = Join-Path $AppDir "deploy\windows\run_http.ps1"
$HttpsScript = Join-Path $AppDir "deploy\windows\run_https.ps1"
$CertFile = Join-Path $AppDir "certs\fullchain.pem"
$WatchdogLog = Join-Path $LogDir "nutrition-watchdog.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-WatchdogLog {
    param([string]$Message)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') $Message" | Out-File -FilePath $WatchdogLog -Append -Encoding utf8
}

function Test-PortOpen {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $asyncResult = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $asyncResult.AsyncWaitHandle.WaitOne(700, $false)) {
            return $false
        }
        $client.EndConnect($asyncResult)
        return $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

Write-WatchdogLog "NutritionApp watchdog started."

while ($true) {
    if (-not (Test-PortOpen -Port 8000)) {
        Write-WatchdogLog "HTTP port 8000 is down; starting NutritionApp HTTP."
        Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$HttpScript`""
        )
        Start-Sleep -Seconds 15
    }

    if ((Test-Path $CertFile) -and -not (Test-PortOpen -Port 443)) {
        Write-WatchdogLog "HTTPS port 443 is down; starting NutritionApp HTTPS."
        Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$HttpsScript`""
        )
        Start-Sleep -Seconds 15
    }

    Start-Sleep -Seconds 60
}
