$ErrorActionPreference = "Continue"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LogDir = Join-Path $AppDir "logs"
$Python = Join-Path $AppDir ".venv\Scripts\python.exe"
$EnvFile = Join-Path $AppDir ".env"
$Port = if ($env:NUTRITION_HTTP_PORT) { $env:NUTRITION_HTTP_PORT } else { "8000" }

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $AppDir
$env:PYTHONUNBUFFERED = "1"

& $Python -m uvicorn nutrition_app.main:app --host 0.0.0.0 --port $Port --env-file $EnvFile 2>&1 |
    Out-File -FilePath (Join-Path $LogDir "nutrition-http.log") -Append -Encoding utf8
