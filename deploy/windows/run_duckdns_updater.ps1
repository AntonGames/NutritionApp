$ErrorActionPreference = "Continue"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$EnvFile = Join-Path $AppDir ".duckdns.env"
$LogDir = Join-Path $AppDir "logs"
$LogFile = Join-Path $LogDir "duckdns-updater.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-DuckDnsLog {
    param([string]$Message)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

function Read-DuckDnsEnv {
    if (-not (Test-Path $EnvFile)) {
        throw "Missing $EnvFile"
    }

    $values = @{}
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        $parts = $line.Split("=", 2)
        if ($parts.Count -eq 2) {
            $values[$parts[0].Trim()] = $parts[1].Trim()
        }
    }

    if (-not $values["DUCKDNS_DOMAIN"] -or -not $values["DUCKDNS_TOKEN"]) {
        throw "DUCKDNS_DOMAIN and DUCKDNS_TOKEN are required in $EnvFile"
    }

    return $values
}

Write-DuckDnsLog "DuckDNS updater started."

while ($true) {
    try {
        $envValues = Read-DuckDnsEnv
        $domain = $envValues["DUCKDNS_DOMAIN"]
        $token = $envValues["DUCKDNS_TOKEN"]
        $url = "https://www.duckdns.org/update?domains=$domain&token=$token&ip="
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
        $content = $response.Content
        if ($content -is [byte[]]) {
            $content = [System.Text.Encoding]::UTF8.GetString($content)
        }
        Write-DuckDnsLog "Update response for $domain`: $($content.ToString().Trim())"
    }
    catch {
        Write-DuckDnsLog "Update failed: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds 300
}
