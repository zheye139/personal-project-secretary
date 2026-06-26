param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$pythonCommand = if (Test-Path -LiteralPath $venvPython) {
    $venvPython
} else {
    "python"
}

$hostAddress = "127.0.0.1"

Write-Host ("API server: http://{0}:{1}" -f $hostAddress, $Port)
Write-Host ("Docs:       http://{0}:{1}/docs" -f $hostAddress, $Port)
Write-Host "Press Ctrl+C to stop the server."
Write-Host ""

Push-Location -LiteralPath $scriptDir
try {
    & $pythonCommand -m uvicorn api_app:app `
        --host $hostAddress `
        --port $Port `
        --no-use-colors
} finally {
    Pop-Location
}
