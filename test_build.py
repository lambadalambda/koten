import unittest

from build import align_old, inline, render_essay, render_index, render_post, render_page

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

    def test_old_forms_get_a_tooltip(self):
        old = '<span class="old" title="1925 edition: %s">%s</span>'
        self.assertEqual(inline('{医師|くすし}の酔', old='醫師の醉'),
                         '<ruby>%s師<rt>くすし</rt></ruby>の%s' % (old % ('醫', '医'), old % ('醉', '酔')))

    def test_old_forms_must_align(self):
        with self.assertRaises(ValueError):
            inline('酔ひ', old='醉')

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


SECTION = {
    'number': 150,
    'title': 'Learning a skill',
    'translation': ['People who want to learn a skill say: not yet.', 'Second.'],
    'original': ['{能|のう}をつかむとする{人|ひと}、「よく」', '二。'],
    'literal': ['A person who tries to acquire a skill, "well"', 'Two.'],
    'notes': [{'quote': '能をつかむ', 'text': '{能|のう}: skill.'}],
}


class EssayTests(unittest.TestCase):
    def test_essay_page_has_reading_and_deeper_layer(self):
        html = render_essay(SECTION, prev=None, next=7)
        main, deeper = html.split('<details', 1)
        self.assertIn('People who want to learn a skill say: not yet.', main)
        self.assertNotIn('A person who tries', main)
        self.assertIn('<ruby>能<rt>のう</rt></ruby>をつかむとする', deeper)
        self.assertIn('A person who tries to acquire a skill', deeper)
        self.assertIn('<dt lang="ja">能をつかむ</dt>', deeper)
        self.assertIn('href="../style.css"', html)

    def test_incipit_is_first_clause_of_original(self):
        html = render_essay(SECTION, prev=None, next=None)
        self.assertIn('<p class="incipit" lang="ja"><ruby>能<rt>のう</rt></ruby>をつかむとする<ruby>人<rt>ひと</rt></ruby></p>', html)

    def test_navigation(self):
        html = render_essay(SECTION, prev=137, next=236)
        self.assertIn('href="137.html"', html)
        self.assertIn('href="236.html"', html)
        self.assertIn('href="index.html"', html)

    def test_original_and_literal_must_align(self):
        with self.assertRaises(ValueError):
            render_essay(dict(SECTION, literal=['only one']), prev=None, next=None)

    def test_essay_marks_old_forms_in_original(self):
        sec = dict(SECTION, original=['{能|のう}をつかむとする{人|ひと}、「よく」', '弐。'])
        html = render_essay(sec, prev=None, next=None, olds=['能をつかむとする人、「よく」', '貳。'])
        self.assertIn('title="1925 edition: 貳"', html)
        self.assertIn('class="legend"', html)
        self.assertNotIn('class="legend"', render_essay(sec, prev=None, next=None))
        same = render_essay(sec, prev=None, next=None, olds=['能をつかむとする人、「よく」', '弐。'])
        self.assertNotIn('class="legend"', same)

    def test_align_old_cuts_edition_text_into_chunks(self):
        self.assertEqual(align_old(['{医|くすし}師', 'の酔'], '醫師の醉'), ['醫師', 'の醉'])
        with self.assertRaises(ValueError):
            align_old(['酔'], '醉ひ')
        self.assertEqual(align_old(['弐'], '貳'), ['貳'])
        with self.assertRaises(ValueError):  # same length, but not an old form of the content
            align_old(['二'], '貳')

    def test_preface_is_named_preface(self):
        self.assertIn('Preface', render_essay(dict(SECTION, number=0), prev=None, next=None))

    def test_comments_are_optional_and_rendered(self):
        comment = {'who': 'Motoori Norinaga', 'where': '玉勝間', 'original': '{花|はな}', 'text': 'He disagrees.'}
        html = render_essay(dict(SECTION, comments=[comment]), prev=None, next=None)
        self.assertIn('Motoori Norinaga', html)
        self.assertIn('He disagrees.', html)

    def test_index_lists_sections_in_order(self):
        html = render_index([dict(SECTION, number=7), SECTION])
        self.assertLess(html.index('href="7.html"'), html.index('href="150.html"'))
        self.assertIn('Learning a skill', html)
