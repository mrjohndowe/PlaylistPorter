from __future__ import annotations

import base64
import json
import os
import queue
import re
import secrets
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from tkinter import filedialog, messagebox, ttk
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlparse

APP_NAME = "Playlist Porter"
SETTINGS_FILE = Path(os.getenv("APPDATA", Path.home())) / "PlaylistPorter" / "settings.json"
INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SPOTIFY_PLAYLIST_RE = re.compile(r"(?:open\.spotify\.com/playlist/|spotify:playlist:)([A-Za-z0-9]+)")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
BROWSER_CHOICES = ("None", "Firefox", "Chrome", "Edge", "Brave", "Opera", "Opera GX")


def resource_path(relative_path: str) -> Path:
    """Resolve an asset in source runs and future bundled application builds."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / relative_path


@dataclass
class Track:
    title: str
    artist: str = ""
    source_url: str | None = None

    @property
    def search_text(self) -> str:
        return f"{self.artist} - {self.title}" if self.artist else self.title


@dataclass
class Playlist:
    name: str
    tracks: list[Track]
    source: str


def safe_folder_name(value: str) -> str:
    cleaned = INVALID_FILE_CHARS.sub("_", value).strip().rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:120] or "Untitled Playlist"


def classify_url(value: str) -> str:
    host = urlparse(value.strip()).netloc.lower().removeprefix("www.")
    if host in {"youtube.com", "music.youtube.com", "youtu.be"}:
        return "youtube"
    if host == "open.spotify.com" or value.strip().startswith("spotify:playlist:"):
        return "spotify"
    raise ValueError("Paste a public Spotify or YouTube playlist link.")


def deno_executable() -> Path:
    """Return the Deno runtime installed beside the active virtual environment."""
    executable_name = "deno.exe" if os.name == "nt" else "deno"
    candidates = [Path(sys.executable).parent / executable_name]
    try:
        import deno

        finder = getattr(deno, "find_deno_exe", None)
        if finder:
            candidates.insert(0, Path(finder()))
    except (ImportError, OSError, TypeError):
        pass
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("The Deno JavaScript runtime is missing. Close the app and run launch.ps1 again to install it.")


def youtube_options(settings: "Settings | None" = None, **overrides: object) -> dict[str, object]:
    options: dict[str, object] = {
        "js_runtimes": {"deno": {"path": str(deno_executable())}},
    }
    if settings and settings.youtube_cookie_file:
        cookie_file = Path(settings.youtube_cookie_file)
        if not cookie_file.is_file():
            raise ValueError("The YouTube cookies file selected in Settings no longer exists.")
        options["cookiefile"] = str(cookie_file)
    elif settings and settings.youtube_cookie_browser:
        options["cookiesfrombrowser"] = browser_cookie_spec(settings.youtube_cookie_browser)
    options.update(overrides)
    return options


def friendly_error(value: object) -> str:
    message = str(value)
    if "Sign in to confirm your age" in message or "age-restricted" in message.lower():
        return (
            "This YouTube video is age-restricted. Open Settings and select a YouTube cookies file "
            "or a signed-in browser. Firefox is the most reliable browser-cookie option on Windows."
        )
    if "Could not copy Chrome cookie database" in message or "Permission denied" in message and "cookie" in message.lower():
        return "Could not read browser cookies. Close the selected browser completely and try again, or select a cookies.txt file in Settings."
    return message


def is_youtube_cookie_domain(domain: str) -> bool:
    normalized = domain.lstrip(".").lower()
    return normalized == "youtube.com" or normalized.endswith(".youtube.com") or normalized == "google.com" or normalized.endswith(".google.com")


def browser_cookie_spec(browser: str) -> tuple[str, str | None, None, None]:
    key = browser.strip().lower().replace(" ", "_")
    if key == "opera_gx":
        profile = Path(os.getenv("APPDATA", Path.home())) / "Opera Software" / "Opera GX Stable"
        return ("opera", str(profile), None, None)
    return (key, None, None, None)


def browser_display_name(browser: str) -> str:
    return "Opera GX" if browser == "opera_gx" else browser.title()


def browser_executable(browser: str) -> Path | None:
    key = browser.strip().lower().replace(" ", "_")
    program_files = Path(os.getenv("ProgramFiles", r"C:\Program Files"))
    program_files_x86 = Path(os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    candidates = {
        "firefox": [program_files / "Mozilla Firefox" / "firefox.exe", program_files_x86 / "Mozilla Firefox" / "firefox.exe"],
        "chrome": [program_files / "Google" / "Chrome" / "Application" / "chrome.exe", program_files_x86 / "Google" / "Chrome" / "Application" / "chrome.exe", local_app_data / "Google" / "Chrome" / "Application" / "chrome.exe"],
        "edge": [program_files_x86 / "Microsoft" / "Edge" / "Application" / "msedge.exe", program_files / "Microsoft" / "Edge" / "Application" / "msedge.exe"],
        "brave": [program_files / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe", program_files_x86 / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe", local_app_data / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe"],
        "opera": [local_app_data / "Programs" / "Opera" / "opera.exe"],
        "opera_gx": [local_app_data / "Programs" / "Opera GX" / "opera.exe"],
    }
    return next((path for path in candidates.get(key, []) if path.is_file()), None)


def open_youtube_in_browser(browser: str) -> None:
    executable = browser_executable(browser)
    if not executable:
        raise ValueError(f"Playlist Porter could not find {browser_display_name(browser)} on this computer.")
    subprocess.Popen([str(executable), "https://www.youtube.com/"], close_fds=True)


def export_youtube_cookies(browser: str, destination: Path) -> int:
    """Export only YouTube/Google cookies from a local browser in Netscape format."""
    from http.cookiejar import MozillaCookieJar
    from yt_dlp.cookies import extract_cookies_from_browser

    browser_name, profile, _, _ = browser_cookie_spec(browser)
    source = extract_cookies_from_browser(browser_name, profile)
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = MozillaCookieJar(str(destination))
    count = 0
    for cookie in source:
        if is_youtube_cookie_domain(cookie.domain):
            output.set_cookie(cookie)
            count += 1
    if not count:
        raise ValueError(f"No YouTube sign-in cookies were found in {browser_display_name(browser)}. Sign into youtube.com in that browser first.")
    output.save(ignore_discard=True, ignore_expires=True)
    return count


class Settings:
    def __init__(self) -> None:
        self.destination = ""
        self.spotify_client_id = ""
        self.spotify_client_secret = ""
        self.spotify_refresh_token = ""
        self.youtube_cookie_file = ""
        self.youtube_cookie_browser = ""
        self.dark_mode = False
        self.load()

    def load(self) -> None:
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            self.destination = data.get("destination", "")
            self.spotify_client_id = data.get("spotify_client_id", "")
            self.spotify_client_secret = data.get("spotify_client_secret", "")
            self.spotify_refresh_token = data.get("spotify_refresh_token", "")
            self.youtube_cookie_file = data.get("youtube_cookie_file", "")
            self.youtube_cookie_browser = data.get("youtube_cookie_browser", "")
            self.dark_mode = bool(data.get("dark_mode", False))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

    def save(self) -> None:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")


class PlaylistService:
    def __init__(self, settings: Settings, status: Callable[[str], None]) -> None:
        self.settings = settings
        self.status = status

    def inspect(self, url: str) -> Playlist:
        source = classify_url(url)
        return self._inspect_youtube(url) if source == "youtube" else self._inspect_spotify(url)

    def _inspect_youtube(self, url: str) -> Playlist:
        import yt_dlp

        self.status("Reading the YouTube playlist…")
        options = youtube_options(self.settings, quiet=True, extract_flat=True, skip_download=True, ignoreerrors=True)
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=False)
        entries = [entry for entry in (info.get("entries") or []) if entry]
        if not entries:
            raise ValueError("No playable videos were found. Make sure the playlist is public.")
        tracks = [Track(entry.get("title") or "Untitled", source_url=entry.get("url")) for entry in entries]
        return Playlist(info.get("title") or "YouTube Playlist", tracks, "YouTube")

    def _spotify_token(self) -> str:
        import requests

        if not self.settings.spotify_client_id or not self.settings.spotify_client_secret:
            raise ValueError("Add Spotify Client ID and Client Secret in Settings before using Spotify links.")
        if self.settings.spotify_refresh_token:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.settings.spotify_refresh_token,
                    "client_id": self.settings.spotify_client_id,
                },
                auth=(self.settings.spotify_client_id, self.settings.spotify_client_secret),
                timeout=20,
            )
            if response.status_code == 200:
                payload = response.json()
                if payload.get("refresh_token"):
                    self.settings.spotify_refresh_token = payload["refresh_token"]
                    self.settings.save()
                return payload["access_token"]
            self.settings.spotify_refresh_token = ""
            self.settings.save()

        self.status("Opening Spotify sign-in in your browser…")
        state = secrets.token_urlsafe(24)
        callback: dict[str, str] = {}

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(handler_self) -> None:
                query = parse_qs(urlparse(handler_self.path).query)
                callback["code"] = query.get("code", [""])[0]
                callback["state"] = query.get("state", [""])[0]
                callback["error"] = query.get("error", [""])[0]
                body = b"<html><body style='font-family:sans-serif;padding:40px'><h2>Spotify connected</h2><p>You can close this window and return to Playlist Porter.</p></body></html>"
                handler_self.send_response(200)
                handler_self.send_header("Content-Type", "text/html; charset=utf-8")
                handler_self.send_header("Content-Length", str(len(body)))
                handler_self.end_headers()
                handler_self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        try:
            server = HTTPServer(("127.0.0.1", 8888), CallbackHandler)
        except OSError as exc:
            raise ValueError("Spotify sign-in could not start because local port 8888 is already in use.") from exc
        server.timeout = 180
        authorize_url = "https://accounts.spotify.com/authorize?" + urlencode({
            "client_id": self.settings.spotify_client_id,
            "response_type": "code",
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "scope": "playlist-read-private",
            "state": state,
            "show_dialog": "true",
        })
        webbrowser.open(authorize_url)
        server.handle_request()
        server.server_close()
        if callback.get("error"):
            raise ValueError(f"Spotify sign-in was not approved: {callback['error']}.")
        if not callback.get("code") or callback.get("state") != state:
            raise ValueError("Spotify sign-in did not complete or the security check failed.")

        raw = f"{self.settings.spotify_client_id}:{self.settings.spotify_client_secret}".encode()
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": "Basic " + base64.b64encode(raw).decode()},
            data={
                "grant_type": "authorization_code",
                "code": callback["code"],
                "redirect_uri": SPOTIFY_REDIRECT_URI,
            }, timeout=20,
        )
        if response.status_code != 200:
            raise ValueError("Spotify could not finish connecting the account. Check the app credentials and Redirect URI.")
        payload = response.json()
        self.settings.spotify_refresh_token = payload.get("refresh_token", "")
        self.settings.save()
        return payload["access_token"]

    def _inspect_spotify(self, url: str) -> Playlist:
        import requests

        match = SPOTIFY_PLAYLIST_RE.search(url)
        if not match:
            raise ValueError("That is not a valid Spotify playlist link.")
        self.status("Reading the Spotify playlist…")
        headers = {"Authorization": f"Bearer {self._spotify_token()}"}
        playlist_id = match.group(1)
        response = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}",
            headers=headers, timeout=20,
        )
        if response.status_code == 403:
            raise ValueError("Spotify now allows playlist tracks only when the signed-in user owns the playlist or is a collaborator.")
        if response.status_code != 200:
            raise ValueError(f"Spotify could not open that playlist (HTTP {response.status_code}). Check the link and account access.")
        data = response.json()
        tracks: list[Track] = []
        page = data.get("items") or data.get("tracks")
        if not isinstance(page, dict):
            raise ValueError("Spotify returned the playlist name but withheld its tracks. Sign in as the playlist owner or a collaborator.")
        while True:
            for item in page.get("items", []):
                track = item.get("item") or item.get("track")
                if track and track.get("name"):
                    tracks.append(Track(track["name"], ", ".join(a["name"] for a in track.get("artists", []))))
            next_url = page.get("next")
            if not next_url:
                break
            page_response = requests.get(next_url, headers=headers, timeout=20)
            page_response.raise_for_status()
            page = page_response.json()
        if not tracks:
            raise ValueError("No tracks were found in that Spotify playlist.")
        return Playlist(data.get("name") or "Spotify Playlist", tracks, "Spotify")

    def download(
        self,
        playlist: Playlist,
        destination: Path,
        cancel_event: threading.Event | None = None,
    ) -> tuple[int, list[str], bool]:
        import imageio_ffmpeg
        import yt_dlp

        cancel_event = cancel_event or threading.Event()
        folder = destination / safe_folder_name(playlist.name)
        folder.mkdir(parents=True, exist_ok=True)
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        failures: list[str] = []
        completed = 0
        cancelled = False
        total = len(playlist.tracks)

        def stop_if_requested(_: dict[str, object]) -> None:
            if cancel_event.is_set():
                raise RuntimeError("Download stopped by user")

        for index, track in enumerate(playlist.tracks, 1):
            if cancel_event.is_set():
                cancelled = True
                break
            self.status(f"Downloading {index} of {total}: {track.search_text}")
            target = str(folder / f"{index:03d} - %(title)s.%(ext)s")
            source = track.source_url or f"ytsearch1:{track.search_text} official audio"
            options = youtube_options(self.settings, **{
                "format": "bestaudio/best", "outtmpl": target, "quiet": True, "noplaylist": True,
                "ignoreerrors": False, "ffmpeg_location": ffmpeg,
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
                "progress_hooks": [stop_if_requested],
                "postprocessor_hooks": [stop_if_requested],
            })
            try:
                with yt_dlp.YoutubeDL(options) as downloader:
                    downloader.download([source])
                if cancel_event.is_set():
                    cancelled = True
                    break
                completed += 1
            except Exception as exc:  # One unavailable track should not stop the playlist.
                if cancel_event.is_set():
                    cancelled = True
                    break
                failures.append(f"{track.search_text}: {friendly_error(exc)}")
        (folder / "playlist-info.json").write_text(json.dumps({
            "name": playlist.name, "source": playlist.source,
            "tracks": [track.__dict__ for track in playlist.tracks], "failures": failures,
            "cancelled": cancelled, "completed_tracks": completed,
        }, indent=2), encoding="utf-8")
        return completed, failures, cancelled


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("980x720")
        self.minsize(820, 620)
        self.settings = Settings()
        self.configure(background="#111522" if self.settings.dark_mode else "#F4F6FA")
        self.window_logo = tk.PhotoImage(file=str(resource_path("assets/playlist-porter-logo.png")))
        self.header_logo = self.window_logo.subsample(16, 16)
        self.iconphoto(True, self.window_logo)
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.cancel_event = threading.Event()
        self.playlist: Playlist | None = None
        self._build_ui()
        self.after(100, self._poll_events)
        if not self.settings.destination:
            self.after(250, self._first_run)

    def _configure_styles(self) -> None:
        palettes = {
            "light": {
                "canvas": "#F4F6FA", "card": "#FFFFFF", "field": "#F8FAFD", "text": "#151B2B",
                "muted": "#65708A", "border": "#D8DEEA", "secondary": "#EEF0F7", "secondary_active": "#E2E5EF",
                "table_heading": "#F7F8FC", "progress_track": "#E9ECF4", "selection": "#EDEBFF",
                "selection_text": "#302A8C", "danger": "#FFF0F0", "danger_active": "#FFE1E3", "danger_text": "#C43D4B",
            },
            "dark": {
                "canvas": "#111522", "card": "#1A2030", "field": "#22293B", "text": "#F4F6FC",
                "muted": "#A4AEC3", "border": "#343D52", "secondary": "#293146", "secondary_active": "#343E57",
                "table_heading": "#222A3C", "progress_track": "#2A3246", "selection": "#3B367A",
                "selection_text": "#FFFFFF", "danger": "#3A2530", "danger_active": "#50303A", "danger_text": "#FF9AA5",
            },
        }
        self.palette = palettes["dark" if self.settings.dark_mode else "light"]
        p = self.palette
        style = ttk.Style(self)
        style.theme_use("clam")
        self.option_add("*Font", ("Segoe UI", 10))
        style.configure("App.TFrame", background=p["canvas"])
        style.configure("Card.TFrame", background=p["card"], relief="flat")
        style.configure("Title.TLabel", background=p["canvas"], foreground=p["text"], font=("Segoe UI Semibold", 26))
        style.configure("Subtitle.TLabel", background=p["canvas"], foreground=p["muted"], font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=p["card"], foreground=p["text"], font=("Segoe UI Semibold", 11))
        style.configure("CardText.TLabel", background=p["card"], foreground=p["muted"])
        style.configure("Status.TLabel", background=p["card"], foreground=p["muted"], font=("Segoe UI Semibold", 9))
        style.configure("Hint.TLabel", background=p["canvas"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure("TEntry", fieldbackground=p["field"], foreground=p["text"], insertcolor=p["text"], bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"], padding=10)
        style.configure("TCombobox", fieldbackground=p["field"], foreground=p["text"], arrowcolor=p["muted"], padding=7)
        style.configure("Card.TCheckbutton", background=p["card"], foreground=p["text"], font=("Segoe UI Semibold", 10))
        style.map("Card.TCheckbutton", background=[("active", p["card"])], indicatorcolor=[("selected", "#625BF6"), ("!selected", p["field"])])
        style.configure("Primary.TButton", background="#625BF6", foreground="#FFFFFF", borderwidth=0, padding=(18, 10), font=("Segoe UI Semibold", 10))
        style.map("Primary.TButton", background=[("active", "#5048E5"), ("disabled", "#B9B6E9")], foreground=[("disabled", "#F2F1FA")])
        style.configure("Secondary.TButton", background=p["secondary"], foreground=p["text"], borderwidth=0, padding=(14, 9), font=("Segoe UI Semibold", 9))
        style.map("Secondary.TButton", background=[("active", p["secondary_active"])])
        style.configure("Danger.TButton", background=p["danger"], foreground=p["danger_text"], borderwidth=0, padding=(14, 9), font=("Segoe UI Semibold", 9))
        style.map("Danger.TButton", background=[("active", p["danger_active"]), ("disabled", p["secondary"])], foreground=[("disabled", p["muted"])])
        style.configure("Modern.Horizontal.TProgressbar", troughcolor=p["progress_track"], background="#625BF6", borderwidth=0, thickness=5)
        style.configure("Treeview", background=p["card"], fieldbackground=p["card"], foreground=p["text"], rowheight=34, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=p["table_heading"], foreground=p["muted"], borderwidth=0, padding=(8, 9), font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", p["selection"])], foreground=[("selected", p["selection_text"])])
        self.configure(background=p["canvas"])

    def _apply_theme(self) -> None:
        self._configure_styles()
        self.logo_label.configure(background=self.palette["canvas"])

    def _build_ui(self) -> None:
        self._configure_styles()

        outer = ttk.Frame(self, padding=(34, 26, 34, 22), style="App.TFrame")
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 20))
        self.logo_label = tk.Label(header, image=self.header_logo, background=self.palette["canvas"], borderwidth=0)
        self.logo_label.pack(side="left", padx=(0, 14), anchor="n")
        brand = ttk.Frame(header, style="App.TFrame")
        brand.pack(side="left", fill="x", expand=True)
        ttk.Label(brand, text="Playlist Porter", style="Title.TLabel").pack(anchor="w")
        ttk.Label(brand, text="Your playlists, organized as local MP3 folders.", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Button(header, text="Settings", style="Secondary.TButton", command=self.open_settings).pack(side="right", anchor="n", pady=4)

        source_card = ttk.Frame(outer, padding=18, style="Card.TFrame")
        source_card.pack(fill="x", pady=(0, 12))
        ttk.Label(source_card, text="PLAYLIST LINK", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 9))
        link_row = ttk.Frame(source_card, style="Card.TFrame")
        link_row.pack(fill="x")
        self.url = tk.StringVar()
        self.url_entry = ttk.Entry(link_row, textvariable=self.url)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _: self.preview())
        self.preview_button = ttk.Button(link_row, text="Preview playlist", style="Primary.TButton", command=self.preview)
        self.preview_button.pack(side="left", padx=(10, 0))

        destination_card = ttk.Frame(outer, padding=(18, 14), style="Card.TFrame")
        destination_card.pack(fill="x", pady=(0, 12))
        destination_row = ttk.Frame(destination_card, style="Card.TFrame")
        destination_row.pack(fill="x")
        destination_copy = ttk.Frame(destination_row, style="Card.TFrame")
        destination_copy.pack(side="left", fill="x", expand=True)
        ttk.Label(destination_copy, text="SAVE LOCATION", style="CardTitle.TLabel").pack(anchor="w")
        self.destination_text = tk.StringVar(value=self.settings.destination or "Choose a destination folder")
        ttk.Label(destination_copy, textvariable=self.destination_text, style="CardText.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Button(destination_row, text="Choose folder", style="Secondary.TButton", command=self.choose_destination).pack(side="right")

        library_card = ttk.Frame(outer, padding=(18, 14, 18, 16), style="Card.TFrame")
        library_card.pack(fill="both", expand=True)
        library_header = ttk.Frame(library_card, style="Card.TFrame")
        library_header.pack(fill="x", pady=(0, 10))
        heading_copy = ttk.Frame(library_header, style="Card.TFrame")
        heading_copy.pack(side="left", fill="x", expand=True)
        ttk.Label(heading_copy, text="PLAYLIST PREVIEW", style="CardTitle.TLabel").pack(anchor="w")
        self.summary = tk.StringVar(value="Paste a YouTube playlist or a Spotify playlist you own or collaborate on.")
        ttk.Label(heading_copy, textvariable=self.summary, style="CardText.TLabel", wraplength=700).pack(anchor="w", pady=(3, 0))
        self.source_badge = tk.Label(library_header, text="  WAITING  ", bg="#EEF0F7", fg="#65708A", font=("Segoe UI Semibold", 8), padx=5, pady=4)
        self.source_badge.pack(side="right", anchor="n")

        list_frame = ttk.Frame(library_card, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.track_list = ttk.Treeview(list_frame, columns=("number", "title", "artist"), show="headings", selectmode="browse")
        self.track_list.heading("number", text="#")
        self.track_list.heading("title", text="TRACK")
        self.track_list.heading("artist", text="ARTIST / SOURCE")
        self.track_list.column("number", width=52, minwidth=52, stretch=False, anchor="center")
        self.track_list.column("title", width=390, minwidth=220)
        self.track_list.column("artist", width=300, minwidth=180)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.track_list.yview)
        self.track_list.configure(yscrollcommand=scrollbar.set)
        self.track_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        progress_row = ttk.Frame(library_card, style="Card.TFrame")
        progress_row.pack(fill="x", pady=(12, 0))
        self.status_text = tk.StringVar(value="Ready")
        ttk.Label(progress_row, textvariable=self.status_text, style="Status.TLabel").pack(side="left", fill="x", expand=True)
        self.progress = ttk.Progressbar(library_card, mode="indeterminate", style="Modern.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(8, 0))

        actions = ttk.Frame(outer, style="App.TFrame")
        actions.pack(fill="x", pady=(14, 0))
        ttk.Label(actions, text="Download only media you own or have permission to save.", style="Hint.TLabel").pack(side="left", anchor="center")
        self.download_button = ttk.Button(actions, text="Create MP3 folder", style="Primary.TButton", command=self.start_download, state="disabled")
        self.download_button.pack(side="right")
        self.stop_button = ttk.Button(actions, text="Stop conversion", style="Danger.TButton", command=self.stop_download, state="disabled")
        self.stop_button.pack(side="right", padx=(0, 10))

        self.url_entry.focus_set()

    def _first_run(self) -> None:
        messagebox.showinfo(APP_NAME, "Choose where playlist folders should be saved. You can change this later.")
        self.choose_destination()

    def choose_destination(self) -> None:
        selected = filedialog.askdirectory(title="Choose where playlist folders will be saved", initialdir=self.settings.destination or str(Path.home()))
        if selected:
            self.settings.destination = selected
            self.settings.save()
            self.destination_text.set(selected)

    def open_settings(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Settings")
        dialog.configure(background=self.palette["canvas"])
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=26, style="Card.TFrame")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Spotify connection", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(frame, text=f"For Spotify playlists, register {SPOTIFY_REDIRECT_URI} as the Redirect URI.", style="CardText.TLabel", wraplength=520).grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 14))
        client_id = tk.StringVar(value=self.settings.spotify_client_id)
        secret = tk.StringVar(value=self.settings.spotify_client_secret)
        cookie_file = tk.StringVar(value=self.settings.youtube_cookie_file)
        cookie_browser = tk.StringVar(value=browser_display_name(self.settings.youtube_cookie_browser) if self.settings.youtube_cookie_browser else "None")
        dark_mode = tk.BooleanVar(value=self.settings.dark_mode)
        ttk.Label(frame, text="Client ID", style="CardText.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=client_id, width=48).grid(row=2, column=1, pady=5)
        ttk.Label(frame, text="Client Secret", style="CardText.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=secret, show="•", width=48).grid(row=3, column=1, pady=5)
        ttk.Separator(frame).grid(row=4, column=0, columnspan=3, sticky="ew", pady=16)
        ttk.Label(frame, text="YouTube sign-in", style="CardTitle.TLabel").grid(row=5, column=0, columnspan=3, sticky="w")
        ttk.Label(frame, text="Optional for restricted videos. A cookies.txt file is most reliable; Firefox is the preferred browser option on Windows.", style="CardText.TLabel", wraplength=520).grid(row=6, column=0, columnspan=3, sticky="w", pady=(3, 12))
        ttk.Label(frame, text="Cookies file", style="CardText.TLabel").grid(row=7, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=cookie_file, width=42).grid(row=7, column=1, sticky="ew", pady=5)
        def choose_cookie_file() -> None:
            selected = filedialog.askopenfilename(parent=dialog, title="Choose a YouTube cookies file", filetypes=[("Cookies text files", "*.txt"), ("All files", "*.*")])
            if selected:
                cookie_file.set(selected)
        ttk.Button(frame, text="Browse", style="Secondary.TButton", command=choose_cookie_file).grid(row=7, column=2, padx=(8, 0), pady=5)
        ttk.Label(frame, text="Or browser", style="CardText.TLabel").grid(row=8, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=cookie_browser, values=BROWSER_CHOICES, state="readonly", width=39).grid(row=8, column=1, sticky="w", pady=5)
        def create_cookie_file() -> None:
            selected_browser = cookie_browser.get().strip().lower().replace(" ", "_")
            if selected_browser == "none":
                messagebox.showwarning(APP_NAME, "Choose the browser where you are signed into YouTube first.", parent=dialog)
                return
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            try:
                open_youtube_in_browser(selected_browser)
            except Exception as exc:
                messagebox.showerror(APP_NAME, friendly_error(exc), parent=dialog)
                return
            browser_name = browser_display_name(selected_browser)
            chromium_note = "\n\nBefore continuing, close every window and background process for this browser so Windows can safely read its cookie database." if selected_browser != "firefox" else ""
            ready = messagebox.askokcancel(
                APP_NAME,
                f"{browser_name} has opened to YouTube.\n\n1. Sign into the age-eligible YouTube account.\n2. Confirm YouTube shows you as signed in.{chromium_note}\n\nSelect OK when you are ready for Playlist Porter to create and save the cookies file.",
                parent=dialog,
            )
            if not ready:
                return
            destination = SETTINGS_FILE.parent / "youtube-cookies.txt"
            try:
                count = export_youtube_cookies(selected_browser, destination)
            except Exception as exc:
                messagebox.showerror(APP_NAME, friendly_error(exc), parent=dialog)
                return
            cookie_file.set(str(destination))
            messagebox.showinfo(
                APP_NAME,
                f"Created and saved the cookies file with {count} YouTube/Google cookies.\n\nSaved to:\n{destination}\n\nIt is now selected for Playlist Porter. Keep this file private like a password.",
                parent=dialog,
            )
        ttk.Button(frame, text="Sign in & create", style="Secondary.TButton", command=create_cookie_file).grid(row=8, column=2, padx=(8, 0), pady=5)
        ttk.Label(frame, text="Choose a browser, then select Sign in & create. Playlist Porter opens YouTube and saves the finished file automatically after sign-in.", style="CardText.TLabel", wraplength=520).grid(row=9, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Separator(frame).grid(row=10, column=0, columnspan=3, sticky="ew", pady=16)
        ttk.Checkbutton(frame, text="Use Dark Mode", variable=dark_mode, style="Card.TCheckbutton").grid(row=11, column=0, columnspan=3, sticky="w")

        def save() -> None:
            credentials_changed = (client_id.get().strip() != self.settings.spotify_client_id or secret.get().strip() != self.settings.spotify_client_secret)
            self.settings.spotify_client_id = client_id.get().strip()
            self.settings.spotify_client_secret = secret.get().strip()
            self.settings.youtube_cookie_file = cookie_file.get().strip()
            selected_browser = cookie_browser.get().strip().lower().replace(" ", "_")
            self.settings.youtube_cookie_browser = "" if selected_browser == "none" else selected_browser
            self.settings.dark_mode = dark_mode.get()
            if credentials_changed:
                self.settings.spotify_refresh_token = ""
            self.settings.save()
            dialog.destroy()
            self._apply_theme()
        ttk.Button(frame, text="Spotify dashboard", style="Secondary.TButton", command=lambda: webbrowser.open("https://developer.spotify.com/dashboard")).grid(row=12, column=0, sticky="w", pady=(18, 0))
        ttk.Button(frame, text="Save settings", style="Primary.TButton", command=save).grid(row=12, column=1, columnspan=2, sticky="e", pady=(18, 0))

    def _set_busy(self, busy: bool) -> None:
        self.preview_button.configure(state="disabled" if busy else "normal")
        self.download_button.configure(state="disabled" if busy or not self.playlist else "normal")
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()
        if not busy:
            self.stop_button.configure(state="disabled")

    def _run(self, operation: Callable[[], object], event: str) -> None:
        self._set_busy(True)
        def worker() -> None:
            try:
                self.events.put((event, operation()))
            except Exception as exc:
                self.events.put(("error", friendly_error(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _status(self, text: str) -> None:
        self.events.put(("status", text))

    def preview(self) -> None:
        url = self.url.get().strip()
        if not url:
            messagebox.showwarning(APP_NAME, "Paste a playlist link first.")
            return
        self._run(lambda: PlaylistService(self.settings, self._status).inspect(url), "previewed")

    def start_download(self) -> None:
        if not self.playlist:
            return
        if not self.settings.destination:
            self.choose_destination()
        if not self.settings.destination:
            return
        playlist = self.playlist
        destination = Path(self.settings.destination)
        self.cancel_event.clear()
        self._run(
            lambda: PlaylistService(self.settings, self._status).download(playlist, destination, self.cancel_event),
            "downloaded",
        )
        self.stop_button.configure(state="normal")

    def stop_download(self) -> None:
        self.cancel_event.set()
        self.stop_button.configure(state="disabled")
        self.status_text.set("Stopping after the current operation…")

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "status":
                    self.status_text.set(str(payload))
                elif event == "error":
                    self._set_busy(False)
                    self.status_text.set("Could not complete the request")
                    messagebox.showerror(APP_NAME, str(payload))
                elif event == "previewed":
                    self.playlist = payload  # type: ignore[assignment]
                    self.track_list.delete(*self.track_list.get_children())
                    for index, track in enumerate(self.playlist.tracks, 1):
                        self.track_list.insert("", "end", values=(f"{index:02d}", track.title, track.artist or self.playlist.source))
                    folder = safe_folder_name(self.playlist.name)
                    self.summary.set(f"{self.playlist.name} · {len(self.playlist.tracks)} tracks · Folder: {folder}")
                    badge_color = "#E9FFF3" if self.playlist.source == "Spotify" else "#FFF1F1"
                    badge_text = "#168A52" if self.playlist.source == "Spotify" else "#C43D4B"
                    self.source_badge.configure(text=f"  {self.playlist.source.upper()}  ", bg=badge_color, fg=badge_text)
                    self.status_text.set("Playlist ready")
                    self._set_busy(False)
                elif event == "downloaded":
                    completed, failures, cancelled = payload  # type: ignore[misc]
                    self._set_busy(False)
                    self.status_text.set("Stopped" if cancelled else "Finished")
                    folder = Path(self.settings.destination) / safe_folder_name(self.playlist.name if self.playlist else "Playlist")
                    detail = f"Saved {completed} MP3 files to:\n{folder}"
                    if cancelled:
                        detail = f"Download stopped. {detail}\n\nCompleted files were kept. You can start the playlist again when ready."
                    if failures:
                        detail += f"\n\n{len(failures)} track(s) could not be downloaded. Details are in playlist-info.json."
                    messagebox.showinfo(APP_NAME, detail)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


if __name__ == "__main__":
    App().mainloop()
