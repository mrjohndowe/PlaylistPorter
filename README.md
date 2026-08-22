# Playlist Porter

Playlist Porter is a Windows desktop app that creates an MP3 folder from a public YouTube playlist or an accessible Spotify playlist. The user chooses a parent destination during first-run setup; each conversion creates a child folder named after the playlist.

## What it does

- Presents a polished card-based desktop interface with a structured track table, source indicator, activity bar, and clearly separated primary, secondary, and stop actions.
- Uses an original Playlist Porter logo—combining a folder, play symbol, and audio levels—in the application header and Windows title bar.
- Includes a persistent **Dark Mode** setting that updates the full interface immediately when saved and restores the selected appearance at the next launch.
- Previews public YouTube playlists and downloads their audio as 192 kbps MP3 files.
- Signs the user into Spotify, reads playlists that user owns or collaborates on through Spotify's official Web API, searches YouTube for each listed track, and saves the matched audio as MP3.
- Numbers tracks in playlist order and writes `playlist-info.json` with source details and any failures.
- Uses a bundled FFmpeg executable supplied by `imageio-ffmpeg`; a separate FFmpeg installation is not required.
- Installs and explicitly configures Deno plus yt-dlp's EJS challenge scripts for current YouTube extraction; users do not need a separate JavaScript runtime installation.
- Continues when an individual track is unavailable.
- Provides a **Stop** button during conversion. Cancellation interrupts active download progress, prevents later tracks from starting, and keeps MP3 files that already finished.
- Supports age-restricted YouTube videos through an optional Netscape-format `cookies.txt` file or cookies read from a signed-in Firefox, Chrome, Edge, Brave, Opera, or Opera GX profile. Cookie use is opt-in and Firefox is the most reliable browser option on Windows.

Spotify does not provide downloadable MP3 audio through its API. Spotify playlist links are used only for titles, artists, ordering, and the playlist name. Since Spotify's February 2026 API changes, playlist contents are returned only when the signed-in user owns the playlist or is a collaborator. The resulting YouTube search match may differ from the Spotify recording, so preview the output. Only download media you own or have permission to save, and follow the source platform's terms.

## Run on Windows

Right-click `launch.ps1` and choose **Run with PowerShell**, or open PowerShell in this folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch.ps1
```

The first launch creates a local `.venv` and installs the three dependencies. Later launches start immediately.

## Spotify setup

YouTube playlists require no account setup. For Spotify playlists:

1. Create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Add `http://127.0.0.1:8888/callback` as the app's Redirect URI.
3. Copy its Client ID and Client Secret.
4. In Playlist Porter, open **Settings**, paste both values, and save.
5. Preview a Spotify playlist and approve the browser sign-in. The app remembers a refresh token so later previews normally do not require another sign-in.

Credentials and the Spotify refresh token are stored for the current Windows user in `%APPDATA%\PlaylistPorter\settings.json`. They are never added to this repository. Spotify may require the signed-in account to be allowlisted in the app's Development Mode user management. Refer to the dashboard if an authorized account still cannot access its own playlist.

## Age-restricted YouTube videos

YouTube requires a signed-in, age-eligible account for restricted videos. Open **Settings** and either select a Netscape-format `cookies.txt` file or choose the browser where YouTube is signed in. A selected file takes precedence over a selected browser. Playlist Porter stores only the file path or browser name; it does not copy browser cookies into its settings file.

For the easiest setup, select the desired browser under **Or browser** and choose **Sign in & create**. Playlist Porter opens that exact browser to YouTube, waits while the user signs in, and then saves `%APPDATA%\PlaylistPorter\youtube-cookies.txt` automatically after confirmation. It exports only YouTube and Google-domain cookies, selects the resulting file, and never exports cookies for unrelated sites. Treat the resulting file like a password.

Firefox is recommended for direct browser-cookie access on Windows. Chromium browsers can lock or restrict cookie decryption; close Chrome, Edge, Brave, Opera, or Opera GX completely before conversion if access fails. Opera GX is mapped to its dedicated `%APPDATA%\Opera Software\Opera GX Stable` profile. Treat exported cookie files like passwords: keep them outside this repository, do not share them, and remove them when no longer needed.

## Tests

After the first launch has prepared the environment:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

These tests cover URL classification and Windows-safe playlist folder naming. A live conversion still depends on network access and the current Spotify/YouTube services.

## Windows installer

Every semantic version tag such as `v1.0.0` triggers `.github/workflows/release.yml`. GitHub Actions runs the tests, builds a standalone Windows application with PyInstaller, packages it with Inno Setup, generates a SHA-256 checksum, and publishes both files on the corresponding GitHub Release.

The installer uses a per-user destination under `%LOCALAPPDATA%\Programs\Playlist Porter`, does not require administrator rights by default, creates a Start Menu shortcut, offers an optional desktop shortcut, and registers an uninstaller. The package includes Python, Deno, FFmpeg, yt-dlp, EJS challenge scripts, and the application logo; end users do not need to install those components separately.

To build version `1.0.0` locally, install Inno Setup 6 and run:

```powershell
.\build-installer.ps1 -Version 1.0.0

```

The resulting installer and checksum are written to `installer\output`. The installer is not Authenticode-signed; Windows will not show a verified publisher until the project adopts a trusted code-signing certificate and signs the final installer before release.

## Automatic updates

Installed builds check the repository's latest GitHub Release shortly after startup when automatic updates are enabled. Playlist Porter compares semantic versions, offers a newer release, downloads the matching installer and `.sha256` file, verifies the installer with SHA-256, and only then launches the silent update and closes the running app. Settings includes both a persistent automatic-update toggle and a manual **Check for updates** action. Development/source runs do not perform automatic startup checks.
