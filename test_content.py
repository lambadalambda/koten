from pathlib import Path
import unittest

from build import align_old, edition_text, load_feed, plain, render_essay, render_page
from kenko_source import sections


class ContentTests(unittest.TestCase):
    def test_every_feed_renders(self):
        files = sorted(Path(__file__).parent.glob('content/*.json'))
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.name):
                feed = load_feed(path)
                ids = [p['id'] for p in feed['posts']]
                self.assertEqual(len(ids), len(set(ids)))
                render_page(feed)



class KenkoContentTests(unittest.TestCase):
    def test_sections_match_the_edition(self):
        root = Path(__file__).parent
        raw = (root / 'sources' / 'tsurezuregusa-wikisource.txt').read_text('utf-8')
        edition, edition_old = sections(raw), sections(raw, modern=False)
        files = sorted(root.glob('content/kenko/*.json'))
        self.assertTrue(files)
        for path in files:
            sec = load_feed(path)
            with self.subTest(section=sec['number']):
                # Chunks may be split freely (e.g. by sentence), but the text must match exactly.
                self.assertEqual(plain(''.join(sec['original'])), edition_text(edition, sec['number']))
                for note in sec['notes']:
                    self.assertIn(note['quote'], plain(''.join(sec['original'])))
                olds = align_old(sec['original'], edition_text(edition_old, sec['number']))
                render_essay(sec, prev=None, next=None, olds=olds)


if __name__ == '__main__':
    unittest.main()
