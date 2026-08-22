# Playlist Porter

Playlist Porter is a Windows desktop app that creates an MP3 folder from a public YouTube playlist or an accessible Spotify playlist. The user chooses a parent destination during first-run setup; each conversion creates a child folder named after the playlist.

## What it does

- Presents a polished card-based desktop interface with a structured track table, source indicator, activity bar, and clearly separated primary, secondary, and stop actions.
- Uses an original Playlist Porter logo—combining a folder, play symbol, and audio levels—in the application header and Windows title bar.
- Previews public YouTube playlists and downloads their audio as 192 kbps MP3 files.
- Signs the user into Spotify, reads playlists that user owns or collaborates on through Spotify's official Web API, searches YouTube for each listed track, and saves the matched audio as MP3.
- Numbers tracks in playlist order and writes `playlist-info.json` with source details and any failures.
- Uses a bundled FFmpeg executable supplied by `imageio-ffmpeg`; a separate FFmpeg installation is not required.
- Installs and explicitly configures Deno plus yt-dlp's EJS challenge scripts for current YouTube extraction; users do not need a separate JavaScript runtime installation.
- Continues when an individual track is unavailable.
- Provides a **Stop** button during conversion. Cancellation interrupts active download progress, prevents later tracks from starting, and keeps MP3 files that already finished.
- Supports age-restricted YouTube videos through an optional Netscape-format `cookies.txt` file or cookies read from a signed-in Firefox, Chrome, Edge, or Brave profile. Cookie use is opt-in and Firefox is the most reliable browser option on Windows.

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

Firefox is recommended for direct browser-cookie access on Windows. Chromium browsers can lock or restrict cookie decryption; close Chrome, Edge, or Brave completely before conversion if access fails. Treat exported cookie files like passwords: keep them outside this repository, do not share them, and remove them when no longer needed.

## Tests

After the first launch has prepared the environment:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

These tests cover URL classification and Windows-safe playlist folder naming. A live conversion still depends on network access and the current Spotify/YouTube services.
