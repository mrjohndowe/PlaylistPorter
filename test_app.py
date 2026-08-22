import unittest
import threading
import tempfile
from pathlib import Path
from unittest.mock import patch

from app import Playlist, PlaylistService, Settings, Track, browser_cookie_spec, browser_display_name, classify_url, deno_executable, is_youtube_cookie_domain, safe_folder_name, youtube_options
from updates import REPOSITORY, is_newer_version, release_from_payload, version_tuple


class AppHelpersTests(unittest.TestCase):
    def test_safe_folder_name_removes_windows_characters(self):
        self.assertEqual(safe_folder_name('Road Trip: 2026 / Favorites?'), 'Road Trip_ 2026 _ Favorites_')

    def test_safe_folder_name_handles_reserved_empty_value(self):
        self.assertEqual(safe_folder_name('...'), 'Untitled Playlist')

    def test_classifies_supported_sources(self):
        self.assertEqual(classify_url('https://open.spotify.com/playlist/abc'), 'spotify')
        self.assertEqual(classify_url('https://www.youtube.com/playlist?list=abc'), 'youtube')

    def test_rejects_other_websites(self):
        with self.assertRaises(ValueError):
            classify_url('https://example.com/playlist')

    def test_youtube_options_configure_deno(self):
        with patch('app.deno_executable', return_value=Path('C:/tools/deno.exe')):
            options = youtube_options(quiet=True)
        self.assertIn('deno', options['js_runtimes'])
        self.assertTrue(options['js_runtimes']['deno']['path'].lower().endswith('deno.exe'))
        self.assertTrue(options['quiet'])

    def test_deno_executable_uses_package_locator(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / 'Scripts' / 'deno.exe'
            executable.parent.mkdir()
            executable.touch()
            with patch('deno.find_deno_bin', return_value=str(executable)):
                self.assertEqual(deno_executable(), executable)

    def test_youtube_options_use_selected_browser_cookies(self):
        settings = Settings()
        settings.youtube_cookie_file = ''
        settings.youtube_cookie_browser = 'firefox'
        with patch('app.deno_executable', return_value=Path('C:/tools/deno.exe')):
            options = youtube_options(settings)
        self.assertEqual(options['cookiesfrombrowser'], ('firefox', None, None, None))

    def test_download_can_stop_before_first_track(self):
        cancel_event = threading.Event()
        cancel_event.set()
        playlist = Playlist('Cancelled list', [Track('Never started')], 'YouTube')
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed, failures, cancelled = PlaylistService(Settings(), lambda _: None).download(
                playlist, Path(temporary_directory), cancel_event
            )
            self.assertEqual(completed, 0)
            self.assertEqual(failures, [])
            self.assertTrue(cancelled)
            report = Path(temporary_directory) / 'Cancelled list' / 'playlist-info.json'
            self.assertTrue(report.is_file())

    def test_settings_dark_mode_defaults_to_boolean(self):
        self.assertIsInstance(Settings().dark_mode, bool)
        self.assertIsInstance(Settings().automatic_updates, bool)

    def test_cookie_export_domain_filter(self):
        self.assertTrue(is_youtube_cookie_domain('.youtube.com'))
        self.assertTrue(is_youtube_cookie_domain('accounts.google.com'))
        self.assertFalse(is_youtube_cookie_domain('.example.com'))

    def test_opera_gx_uses_opera_extractor_and_gx_profile(self):
        browser, profile, keyring, container = browser_cookie_spec('opera_gx')
        self.assertEqual(browser, 'opera')
        self.assertTrue(profile.endswith(r'Opera Software\Opera GX Stable'))
        self.assertIsNone(keyring)
        self.assertIsNone(container)

    def test_browser_display_name_preserves_opera_gx(self):
        self.assertEqual(browser_display_name('opera_gx'), 'Opera GX')

    def test_update_versions_are_compared_semantically(self):
        self.assertEqual(version_tuple('v1.2.3'), (1, 2, 3))
        self.assertTrue(is_newer_version('1.10.0', '1.9.9'))
        self.assertFalse(is_newer_version('1.0.0', '1.0.0'))

    def test_updates_use_renamed_repository(self):
        self.assertEqual(REPOSITORY, 'mrjohndowe/PlaylistPorter')

    def test_release_requires_installer_and_checksum(self):
        payload = {
            'tag_name': 'v1.2.3',
            'html_url': 'https://example.test/release',
            'assets': [
                {'name': 'Playlist-Porter-v1.2.3-Setup.exe', 'browser_download_url': 'https://example.test/setup'},
                {'name': 'Playlist-Porter-v1.2.3-Setup.exe.sha256', 'browser_download_url': 'https://example.test/hash'},
            ],
        }
        release = release_from_payload(payload)
        self.assertEqual(release.version, '1.2.3')
        self.assertEqual(release.installer_name, 'Playlist-Porter-v1.2.3-Setup.exe')


if __name__ == '__main__':
    unittest.main()
