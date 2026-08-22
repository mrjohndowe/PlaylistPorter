from __future__ import annotations

import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests


REPOSITORY = "mrjohndowe/PlaylistPorter"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    page_url: str
    installer_url: str
    installer_name: str
    checksum_url: str


def version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid release version: {value}")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def is_newer_version(candidate: str, current: str) -> bool:
    return version_tuple(candidate) > version_tuple(current)


def release_from_payload(payload: dict[str, object]) -> ReleaseInfo:
    tag = str(payload.get("tag_name", ""))
    version_tuple(tag)
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise ValueError("The GitHub Release does not contain downloadable assets.")
    installer_name = f"Playlist-Porter-{tag}-Setup.exe"
    installer = next((asset for asset in assets if isinstance(asset, dict) and asset.get("name") == installer_name), None)
    checksum = next((asset for asset in assets if isinstance(asset, dict) and asset.get("name") == f"{installer_name}.sha256"), None)
    if not installer or not checksum:
        raise ValueError("The latest release is missing its installer or SHA-256 checksum.")
    return ReleaseInfo(
        version=tag.lstrip("v"),
        tag=tag,
        page_url=str(payload.get("html_url", f"https://github.com/{REPOSITORY}/releases/tag/{tag}")),
        installer_url=str(installer["browser_download_url"]),
        installer_name=installer_name,
        checksum_url=str(checksum["browser_download_url"]),
    )


def latest_release(timeout: int = 15) -> ReleaseInfo:
    response = requests.get(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        timeout=timeout,
    )
    response.raise_for_status()
    return release_from_payload(response.json())


def download_verified_installer(release: ReleaseInfo, timeout: int = 60) -> Path:
    update_directory = Path(tempfile.gettempdir()) / "PlaylistPorterUpdates" / release.version
    update_directory.mkdir(parents=True, exist_ok=True)
    destination = update_directory / release.installer_name
    checksum_response = requests.get(release.checksum_url, timeout=timeout)
    checksum_response.raise_for_status()
    expected_hash = checksum_response.text.strip().split()[0].lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("The release checksum file is invalid.")
    digest = hashlib.sha256()
    with requests.get(release.installer_url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
                    digest.update(chunk)
    if digest.hexdigest().lower() != expected_hash:
        destination.unlink(missing_ok=True)
        raise ValueError("The downloaded update failed SHA-256 verification and was removed.")
    return destination
