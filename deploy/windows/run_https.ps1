$ErrorActionPreference = "Continue"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LogDir = Join-Path $AppDir "logs"
$Python = Join-Path $AppDir ".venv\Scripts\python.exe"
$EnvFile = Join-Path $AppDir ".env"
$CertFile = Join-Path $AppDir "certs\fullchain.pem"
$KeyFile = Join-Path $AppDir "certs\privkey.pem"
$Port = if ($env:NUTRITION_HTTPS_PORT) { $env:NUTRITION_HTTPS_PORT } else { "443" }

if (-not (Test-Path $CertFile) -or -not (Test-Path $KeyFile)) {
    throw "Missing TLS certificate files in $AppDir\certs"
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $AppDir
$env:PYTHONUNBUFFERED = "1"

& $Python -m uvicorn nutrition_app.main:app --host 0.0.0.0 --port $Port --env-file $EnvFile --ssl-certfile $CertFile --ssl-keyfile $KeyFile 2>&1 |
    Out-File -FilePath (Join-Path $LogDir "nutrition-https.log") -Append -Encoding utf8
