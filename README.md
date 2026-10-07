# Heian timeline

Classical Japanese texts presented as social-media threads, for English speakers who are curious about Japanese. Each post has three layers: a free modern English version, the original text with furigana, and a literal translation with notes.

```sh
python3 build.py              # writes site/*.html from content/*.json
python3 -m unittest -v        # renderer and content checks
```

Open `site/nikuki-mono.html` in a browser. No JavaScript, no dependencies.

## Content format

One JSON file per feed in `content/`. Furigana markup: `{漢字|かんじ}`. Plain text must not contain `{`, `}` or `|`. Posts can set `reply_to` to another post id. Source URLs must be http(s).

Original texts are public domain. Modern translations are not: all English text here is our own.
