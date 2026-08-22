import unittest
import threading
import tempfile
from pathlib import Path

from app import Playlist, PlaylistService, Settings, Track, classify_url, safe_folder_name, youtube_options


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
        options = youtube_options(quiet=True)
        self.assertIn('deno', options['js_runtimes'])
        self.assertTrue(options['js_runtimes']['deno']['path'].lower().endswith('deno.exe'))
        self.assertTrue(options['quiet'])

    def test_youtube_options_use_selected_browser_cookies(self):
        settings = Settings()
        settings.youtube_cookie_file = ''
        settings.youtube_cookie_browser = 'firefox'
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


if __name__ == '__main__':
    unittest.main()
