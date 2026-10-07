# koten

Japanese classics for English speakers who are curious about Japanese. Each page has a clean, readable English translation first, and a "dig deeper" layer with the original text (furigana, historical kana), a literal translation and notes.

- `content/kenko/`: Tsurezuregusa by Yoshida Kenkō, one file per section. Text from the 1925 edition (校註日本文學大系), via Wikisource, in `sources/`.
- `content/nikuki-mono.json`: an experiment, Sei Shōnagon's にくきもの as a social-media thread.

```sh
python3 build.py              # writes site/ from content/
python3 -m unittest -v        # renderer, source cleaner, and content checks
```

Open `site/kenko/index.html` in a browser. No JavaScript, no dependencies.

## Writing content

- Read `STYLE.md` before writing translations.
- Furigana markup: `{漢字|かんじ}`. Plain text must not contain `{`, `}` or `|`.
- `python3 kenko_source.py sources/tsurezuregusa-wikisource.txt 150` prints the cleaned text of a section. The content test checks that every section's original, without furigana, is exactly this text.
- Every note needs a `quote` that occurs in the original.
- Experiments: a section can have `"variants": {"name": [paragraph or null, …]}` to try another translation for single paragraphs. `python3 build.py --variant name` builds with it; the normal build ignores it.

Original texts are public domain. Modern translations are not: all English text here is our own.
