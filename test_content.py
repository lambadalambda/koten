from pathlib import Path
import unittest

from build import load_feed, render_page


class ContentTests(unittest.TestCase):
    def test_every_content_file_renders(self):
        files = sorted(Path(__file__).parent.glob('content/*.json'))
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.name):
                feed = load_feed(path)
                ids = [p['id'] for p in feed['posts']]
                self.assertEqual(len(ids), len(set(ids)))
                render_page(feed)


if __name__ == '__main__':
    unittest.main()
