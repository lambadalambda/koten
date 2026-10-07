import unittest

from kenko_source import (clean, expand_iteration, remove_glosses, sections,
                          to_shinjitai)


class GlossTests(unittest.TestCase):
    def test_removes_glosses(self):
        self.assertEqual(remove_glosses('日ぐらし{{smaller|〔終日〕}}硯'), '日ぐらし硯')

    def test_removes_nested_glosses(self):
        raw = '聖海上人{{smaller|〔不明傳{{smaller|〈＊ママ〉}}〕}}、その外'
        self.assertEqual(remove_glosses(raw), '聖海上人、その外')

    def test_unbalanced_template_is_an_error(self):
        with self.assertRaises(ValueError):
            remove_glosses('a{{smaller|〔b〕')


class IterationTests(unittest.TestCase):
    def test_single_marks(self):
        self.assertEqual(expand_iteration('たゝ'), 'たた')
        self.assertEqual(expand_iteration('たゞ'), 'ただ')
        self.assertEqual(expand_iteration('いかゞ'), 'いかが')

    def test_double_marks_repeat_two_kana(self):
        self.assertEqual(expand_iteration('おの〳〵'), 'おのおの')
        self.assertEqual(expand_iteration('つれ〴〵'), 'つれづれ')
        self.assertEqual(expand_iteration('這ふ〳〵'), '這ふ這ふ')

    def test_single_mark_repeats_unvoiced_kana(self):
        self.assertEqual(expand_iteration('づゝ'), 'づつ')
        self.assertEqual(expand_iteration('ずゝ'), 'ずず')

    def test_three_kana_units_use_overrides(self):
        self.assertEqual(clean('かへす{{〲}}口惜しき'), 'かへすがへす口惜しき')
        self.assertEqual(clean('あさな{{〱}}'), 'あさなあさな')

    def test_mark_after_non_kana_is_an_error(self):
        with self.assertRaises(ValueError):
            expand_iteration('}ゝ')


class CleanTests(unittest.TestCase):
    def test_shinjitai(self):
        self.assertEqual(to_shinjitai('醉ひて醫師'), '酔ひて医師')
        self.assertEqual(to_shinjitai('飮遙棊'), '飲遥碁')

    def test_clean_pipeline(self):
        raw = 'つれ{{〲}}なるまゝに{{smaller|〔退屈なので〕}}、{{r|一年|ひととせ}}を覺え'
        self.assertEqual(clean(raw), 'つれづれなるままに、{一年|ひととせ}を覚え')

    def test_sic_marks_are_removed_from_readings(self):
        self.assertEqual(clean('{{r|江|え－ママ}}'), '{江|え}')

    def test_spaces_are_removed(self):
        self.assertEqual(clean('」 と　ぞ'), '」とぞ')

    def test_iteration_mark_inside_reading(self):
        self.assertEqual(clean('{{r|愈|いよ{{〱}}}}よく'), '{愈|いよいよ}よく')

    def test_unknown_template_is_an_error(self):
        with self.assertRaises(ValueError):
            clean('a{{foo}}b')


class RealSourceTests(unittest.TestCase):
    def test_full_text_has_no_leftovers(self):
        from pathlib import Path
        raw = (Path(__file__).parent / 'sources' / 'tsurezuregusa-wikisource.txt').read_text('utf-8')
        text = ''.join(''.join(p) for p in sections(raw).values())
        for bad in ['ママ', '〔', '〕', '{{', 'ゝ', 'ゞ', '〳', '〴', '〵', ' ', '　'] + list('讚劒鬭舍稻艷寳穩祿晉畧醉覺'):
            self.assertNotIn(bad, text)


class SectionTests(unittest.TestCase):
    RAW = '{{header\n| x = y\n}}\n\n1\n\n序の文。\n\nいでや、一の文。\n\n2\n\n二の文。\n\n二の続き。\n\n\n徒然草 終\n\n{{PD-old-50-1996|deathyear=1943}}\n'

    def test_preface_is_split_from_section_one(self):
        secs = sections(self.RAW)
        self.assertEqual(secs[0], ['序の文。'])
        self.assertEqual(secs[1], ['いでや、一の文。'])
        self.assertEqual(secs[2], ['二の文。', '二の続き。'])


if __name__ == '__main__':
    unittest.main()
