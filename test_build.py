import unittest

from build import inline, render_post, render_page

ACCOUNTS = {
    'sei': {'name': 'Sei Shōnagon', 'handle': '@sei_shonagon', 'jp': '清少納言'},
    'murasaki': {'name': 'Murasaki Shikibu', 'handle': '@murasaki', 'jp': '紫式部'},
}
POST = {
    'id': 'p1', 'author': 'sei', 'date': 'c. 1000',
    'text': 'things i hate\na thread',
    'original': '{蚊|か}の{細声|ほそごゑ}',
    'literal': 'A mosquito, in a thin voice.',
    'notes': ['{蚊|か} is a mosquito.'],
}


class InlineTests(unittest.TestCase):
    def test_ruby_markup(self):
        self.assertEqual(inline('{蚊|か}の声'), '<ruby>蚊<rt>か</rt></ruby>の声')

    def test_plain_text_unchanged(self):
        self.assertEqual(inline('にくきもの。'), 'にくきもの。')

    def test_escapes_html_everywhere(self):
        self.assertEqual(inline('<b>{&|<}'), '&lt;b&gt;<ruby>&amp;<rt>&lt;</rt></ruby>')

    def test_newlines_become_breaks(self):
        self.assertEqual(inline('a\nb'), 'a<br>b')
        self.assertEqual(inline('a\r\nb'), 'a<br>b')

    def test_malformed_markup_is_an_error(self):
        for bad in ['{蚊か}', '{蚊|か', '蚊|か}', '{|か}', '{蚊|}']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                inline(bad)


class RenderTests(unittest.TestCase):
    def test_post_has_three_layers(self):
        html = render_post(POST, ACCOUNTS, {})
        self.assertIn('things i hate<br>a thread', html)
        self.assertIn('<ruby>細声<rt>ほそごゑ</rt></ruby>', html)
        self.assertIn('A mosquito, in a thin voice.', html)
        self.assertIn('<li><ruby>蚊<rt>か</rt></ruby> is a mosquito.</li>', html)
        self.assertEqual(html.count('<details'), 2)

    def test_post_shows_author(self):
        html = render_post(POST, ACCOUNTS, {})
        self.assertIn('Sei Shōnagon', html)
        self.assertIn('@sei_shonagon', html)
        self.assertIn('lang="ja"', html)

    def test_reply_names_the_quoted_account(self):
        reply = dict(POST, id='p2', author='murasaki', reply_to='p1')
        html = render_post(reply, ACCOUNTS, {'p1': POST})
        self.assertIn('Replying to <a href="#p1">@sei_shonagon</a>', html)

    def test_reply_to_unknown_post_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'p2.*zz'):
            render_post(dict(POST, id='p2', reply_to='zz'), ACCOUNTS, {})

    def test_unknown_author_is_an_error(self):
        with self.assertRaises(KeyError):
            render_post(dict(POST, author='nobody'), ACCOUNTS, {})

    def feed(self, **changes):
        feed = {
            'title': 'T <&>', 'intro': 'i', 'accounts': ACCOUNTS,
            'posts': [POST, dict(POST, id='p2', text='second')],
            'sources': [{'label': 'Src', 'url': 'https://example.org/'}],
        }
        return dict(feed, **changes)

    def test_page_keeps_post_order_and_sources(self):
        html = render_page(self.feed())
        self.assertLess(html.index('id="p1"'), html.index('id="p2"'))
        self.assertIn('href="https://example.org/"', html)
        self.assertTrue(html.startswith('<!doctype html>'))

    def test_title_is_escaped(self):
        html = render_page(self.feed())
        self.assertIn('<title>T &lt;&amp;&gt;</title>', html)
        self.assertIn('<h1>T &lt;&amp;&gt;</h1>', html)

    def test_only_web_urls_in_sources(self):
        with self.assertRaises(ValueError):
            render_page(self.feed(sources=[{'label': 'x', 'url': 'javascript:alert(1)'}]))

    def test_duplicate_post_ids_are_an_error(self):
        with self.assertRaisesRegex(ValueError, 'p1'):
            render_page(self.feed(posts=[POST, POST]))


if __name__ == '__main__':
    unittest.main()
