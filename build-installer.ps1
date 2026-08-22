param(
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    py -3 -m venv (Join-Path $projectDirectory ".venv")
}

& $python -m pip install -r (Join-Path $projectDirectory "requirements.txt") -r (Join-Path $projectDirectory "requirements-build.txt")
& $python -m unittest -v
& $python (Join-Path $projectDirectory "scripts\create_icon.py")
& $python -m PyInstaller --noconfirm --clean (Join-Path $projectDirectory "PlaylistPorter.spec")

$compilerCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
)
$compiler = $compilerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $compiler) {
    throw "Inno Setup 6 is required to build the installer. Install it from https://jrsoftware.org/isdl.php and run this script again."
}

& $compiler "/DAppVersion=$Version" (Join-Path $projectDirectory "installer\PlaylistPorter.iss")
$installer = Join-Path $projectDirectory "installer\output\Playlist-Porter-v$Version-Setup.exe"
$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $installer
"$($hash.Hash.ToLowerInvariant())  $([IO.Path]::GetFileName($installer))" | Set-Content -Encoding ascii "$installer.sha256"

Write-Host "Installer created: $installer"
Write-Host "Checksum created: $installer.sha256"

