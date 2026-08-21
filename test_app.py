import unittest

from app import classify_url, safe_folder_name


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


if __name__ == '__main__':
    unittest.main()

