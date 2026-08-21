$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$virtualEnvironment = Join-Path $projectDirectory ".venv"
$python = Join-Path $virtualEnvironment "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Preparing Playlist Porter for first use..."
    py -3 -m venv $virtualEnvironment
    & $python -m pip install --upgrade pip
    & $python -m pip install -r (Join-Path $projectDirectory "requirements.txt")
}

& $python (Join-Path $projectDirectory "app.py")

