from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH)
datas = [(str(project_root / "assets" / "playlist-porter-logo.png"), "assets")]
binaries = []
hiddenimports = []

for package in ("yt_dlp", "yt_dlp_ejs", "imageio_ffmpeg", "deno"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

deno_exe = Path(sys.executable).parent / "deno.exe"
if not deno_exe.is_file():
    raise SystemExit(f"Deno was not found at {deno_exe}. Install requirements.txt before building.")
binaries.append((str(deno_exe), "."))

a = Analysis(
    [str(project_root / "app.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PlaylistPorter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "build" / "playlist-porter.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="PlaylistPorter",
)

