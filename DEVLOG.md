# Devlog

## 2026-10-07: prototype にくきもの

- Idea: Sei Shōnagon's lists read like threads, Kenkō reads like a blog, and Murasaki's diary comment on Sei Shōnagon reads like a subtweet.
- Murasaki and Sei Shōnagon were probably never at court together (Sei Shōnagon left c. 1000/01, Murasaki came c. 1005/06), so the "feud" is one-sided. This is part of the joke, and a note says so.
- Text source: manapedia.jp, which names three modern editions as its basis (Hagitani 1977, Matsuo and Nagai 1989, Watanabe 1991). I did not verify which manuscript line it follows. Manuscript lines differ in small details (e.g. まらうと/まらうど, さすがに present or not), so always name the text you follow.
- Furigana use historical kana to match the text. Grammar terms in notes use modern readings.
- Static HTML with `<details>` for the layers, so no JavaScript is needed.
- Content is the risky part, not code: every content change gets a fact-check against the source text.

## 2026-10-08: Kenkō pilot

- Base text: Wikisource transcription of 校註日本文學大系 vol. 3 (1925), public domain, stored in `sources/`. `kenko_source.py` removes the editor's 〔〕 glosses, keeps its readings as furigana, expands iteration marks, and modernizes old kanji. Historical kana stays.
- The 2-character rule for 〳〵 is wrong in 4 places (e.g. かへす〴〵); these are listed in `OVERRIDES`. ゝ after a voiced kana repeats the unvoiced kana (づゝ → づつ), except 数珠 ずゝ.
- `test_content.py` checks that each section's original, without furigana, is exactly the edition text. So furigana work can never change the text.
- Format: clean translation first; "dig deeper" holds sentence pairs (original + literal) and notes anchored to quotes. Humour only where the original has it.
- Fact-checks found mostly grammar-term slips in notes (e.g. 召させむ is 召さ + せ, not さす; めり is "it seems", not hearsay). Readings that come from the 1925 edition itself (e.g. 三足 さんぞく) are kept even when other editions differ.
- Old kanji on hover: the cleaner can keep the 1925 forms (`modern=False`). Old and modern texts align character by character, because the conversion is a 1:1 mapping and runs after iteration marks are expanded. `align_old` checks that the old text, converted, equals the content text, so an edit to the content can never be shown as an "old form".

## Ideas for later

- Heike Monogatari: Momus's "Bishonen" (1988) as a "later readers" note, especially for the death of Atsumori. Same theme (the beautiful youth who dies young, falling blossoms), and the song is a model for the voice: Japanese ideals in a flat British voice. Link only, no lyric quotes (copyright).
- Open: Kenkō 6, Shōtoku's tomb. ここをきれ、かしこを断て is now "Cut it here. Cut it off there." Clear enough, but not fully satisfying. Revisit if a better English pair comes up.
- Christian reader / Ecclesiastes (aside, not planned): for a Christian reader "this world" carries the この世/後の世 contrast without a note ("in the world but not of the world", contemptus mundi). Ecclesiastes is close to Kenkō in places: "vanity of vanities", "a time to be born, and a time to die", the man who builds and cannot keep it (sections 7, 10, end of 137 as memento mori). But the frame imports a creator, sin and salvation: 後の世 is the next rebirth or the Pure Land, not heaven, and for Kenkō impermanence is what makes things beautiful, not a fallen world. Same vocabulary, wrong attitude. Older English translations may lean this way because King James English was the default "serious" register. Possible experiment via `variants` (e.g. a King James version of section 7), not the main voice.
- Borges, "Pierre Menard, Author of the Quixote": Kenkō 14 makes the same observation with the opposite judgement. Poets use the same words and famous places (同じことば歌枕), but the old poems are "not the same thing at all". Same words, different time, different poem. It also describes the project: the Japanese text is fixed (and tested), everything around it is new. Not for the notes, which stay with what Kenkō could have known.

## 2026-10-08/09: the rest of the book overnight

- Sections 37–243 (202 sections) written in 17 batches of about 12. For each batch: a writer agent (STYLE.md + approved reference sections), then an independent checker agent with permission to fix, then a batch check (text identical to the edition, note quotes, rendering) and a separate commit.
- Checkers compared with roudokus.com and, from the 11th batch on, with the 1925 editor's own glosses in the raw source, which turned out to be a useful second authority. Where they disagree, notes give both.
- Typical checker fixes: invented setup or examples in translations, mind-reading in notes, facts stated from memory (removed or hedged), wrong subjects in ambiguous sentences, grand titles, exotic terms.
- Cleaner bug found by a writer: おどろ〳〵 is a 3-kana unit (added to OVERRIDES).
- Open points for the human reviewer are collected in REVIEW.md, by batch.
