from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import build
from build import align_old, apply_variant, edition_text, load_feed, plain, render_essay, render_index, render_page
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
        files = sorted(root.glob('content/kenko/[0-9]*.json'))
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
                for name in sec.get('variants', {}):
                    render_essay(apply_variant(sec, name), prev=None, next=None, olds=olds)


    def test_book_intro_renders(self):
        book = load_feed(Path(__file__).parent / 'content' / 'kenko' / 'book.json')
        self.assertIn('Kenkō', render_index([], book))


class BuildTests(unittest.TestCase):
    def test_build_has_a_root_entry_point(self):
        source = Path(__file__).parent
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('content', 'sources'):
                shutil.copytree(source / name, root / name)
            shutil.copy(source / 'style.css', root / 'style.css')
            with patch.object(build, 'ROOT', root), redirect_stdout(StringIO()):
                build.main()
            site = root / 'site'
            home = (site / 'index.html').read_text('utf-8')
            self.assertIn('Tsurezuregusa', home)
            self.assertIn('href="kenko/index.html"', home)
            self.assertIn('href="style.css"', home)
            self.assertTrue((site / 'style.css').is_file())
            contents = (site / 'kenko' / 'index.html').read_text('utf-8')
            self.assertIn('href="../style.css"', contents)
            self.assertIn('href="0.html"', contents)
            for number in range(244):
                self.assertTrue((site / 'kenko' / f'{number}.html').is_file())


if __name__ == '__main__':
    unittest.main()
