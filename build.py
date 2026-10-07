#!/usr/bin/env python3
"""Render content/*.json feeds into static HTML pages in site/."""
from itertools import accumulate
import html
import json
from pathlib import Path
import re
import shutil

from kenko_source import SHINJITAI, sections

ROOT = Path(__file__).parent
RUBY = re.compile(r'\{([^{}|]+)\|([^{}|]+)\}')


def inline(text, old=None):
    """Escape text; turn {base|reading} into <ruby> and newlines into <br>.

    old: the same text without markup, but with the edition's old kanji forms.
    Characters that differ get a tooltip with the old form.
    """
    if old is not None and len(old) != len(plain(text)):
        raise ValueError('Old-form text does not align with: %r' % text[:30])
    chars = _chars(iter(old or ''))
    parts, pos = [], 0
    for m in RUBY.finditer(text):
        parts.append(chars(_checked(text[pos:m.start()])))
        parts.append('<ruby>%s<rt>%s</rt></ruby>' % (chars(m[1]), html.escape(m[2])))
        pos = m.end()
    parts.append(chars(_checked(text[pos:])))
    return '<br>'.join(''.join(parts).splitlines())


def _checked(text):
    if any(c in text for c in '{}|'):
        raise ValueError('Malformed ruby markup near: %r' % text)
    return text


def _chars(olds):
    """Return a function that escapes text segments in order, marking characters whose old form differs."""
    def chars(segment):
        return ''.join(html.escape(c, quote=False) if (o := next(olds, c)) == c else
                       '<span class="old" title="1925 edition: %s">%s</span>' % (html.escape(o), html.escape(c))
                       for c in segment)
    return chars


def render_post(post, accounts, by_id):
    acc = accounts[post['author']]
    reply = ''
    if post.get('reply_to'):
        if post['reply_to'] not in by_id:
            raise ValueError('Post %s replies to unknown post %r' % (post['id'], post['reply_to']))
        target = accounts[by_id[post['reply_to']]['author']]
        reply = '<p class="reply">Replying to <a href="#%s">%s</a></p>' % (
            html.escape(post['reply_to']), html.escape(target['handle']))
    notes = ''.join('<li>%s</li>' % inline(n) for n in post['notes'])
    return (
        '<article class="post %(author)s" id="%(id)s">'
        '<header><span class="name">%(name)s</span> <span class="jp" lang="ja">%(jp)s</span> '
        '<span class="handle">%(handle)s</span> · <span class="date">%(date)s</span></header>'
        '%(reply)s<p class="text">%(text)s</p>'
        '<details class="original"><summary>原文 · original</summary>'
        '<p lang="ja">%(original)s</p></details>'
        '<details class="notes"><summary>Literal translation &amp; notes</summary>'
        '<p class="literal">%(literal)s</p><ul>%(notes)s</ul></details>'
        '</article>'
    ) % {
        'author': html.escape(post['author']), 'id': html.escape(post['id']),
        'name': html.escape(acc['name']), 'jp': html.escape(acc['jp']),
        'handle': html.escape(acc['handle']), 'date': html.escape(post['date']),
        'reply': reply, 'text': inline(post['text']), 'original': inline(post['original']),
        'literal': inline(post['literal']), 'notes': notes,
    }


def render_page(feed):
    by_id = {}
    for p in feed['posts']:
        if p['id'] in by_id:
            raise ValueError('Duplicate post id %r' % p['id'])
        by_id[p['id']] = p
    if not all(s['url'].startswith(('https://', 'http://')) for s in feed['sources']):
        raise ValueError('Source URLs must be http(s)')
    posts = '\n'.join(render_post(p, feed['accounts'], by_id) for p in feed['posts'])
    sources = ''.join('<li><a href="%s">%s</a></li>' % (html.escape(s['url']), inline(s['label']))
                      for s in feed['sources'])
    body = '<h1>%s</h1><p class="intro">%s</p>\n%s\n<footer><h2>Sources</h2><ul>%s</ul></footer>' % (
        html.escape(feed['title']), inline(feed['intro']), posts, sources)
    return page(feed['title'], body)


def page(title, body, css='style.css'):
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>%s</title><link rel="stylesheet" href="%s"></head><body><main>%s</main></body></html>\n'
    ) % (html.escape(title), html.escape(css), body)


def plain(text):
    """Text without furigana markup."""
    return RUBY.sub(r'\1', text)


def align_old(original, old_text):
    """Cut the edition's old-form text into the same chunks as the original."""
    text = ''.join(plain(o) for o in original)
    if old_text.translate(SHINJITAI) != text:
        raise ValueError('Original does not match the edition (%d vs %d characters)' % (len(text), len(old_text)))
    bounds = list(accumulate([0] + [len(plain(o)) for o in original]))
    return [old_text[a:b] for a, b in zip(bounds, bounds[1:])]


def edition_text(edition, number):
    """One section of the edition as plain text."""
    return plain(''.join(edition[number]))


def section_name(number):
    return 'Preface' if number == 0 else 'Section %d' % number


def incipit(original):
    """The opening words of a section, up to the first 、 or 。."""
    first = original[0]
    end = min((i for i in (first.find('、'), first.find('。')) if i >= 0), default=len(first))
    return first[:end]


def render_essay(sec, prev, next, olds=None):
    if len(sec['original']) != len(sec['literal']):
        raise ValueError('Section %s: original and literal need the same number of paragraphs' % sec['number'])
    nav = '<nav>%s<a href="index.html">Contents</a>%s</nav>' % (
        '' if prev is None else '<a href="%d.html">← %s</a> · ' % (prev, section_name(prev)),
        '' if next is None else ' · <a href="%d.html">%s →</a>' % (next, section_name(next)))
    legend = ('<p class="legend">Kanji with a dotted underline are printed in an older form in the 1925 edition. '
              'On a computer, hover over them to see it.</p>'
              if olds and any(plain(o) != od for o, od in zip(sec['original'], olds)) else '')
    olds = olds or [None] * len(sec['original'])
    pairs = ''.join('<div class="pair"><p lang="ja">%s</p><p class="literal">%s</p></div>' % (inline(o, od), inline(l))
                    for o, od, l in zip(sec['original'], olds, sec['literal']))
    notes = ''.join('<dt lang="ja">%s</dt><dd>%s</dd>' % (html.escape(n['quote']), inline(n['text']))
                    for n in sec['notes'])
    comments = ''.join(
        '<div class="comment"><p class="who">%s <span lang="ja">%s</span></p><p lang="ja">%s</p><p>%s</p></div>'
        % (html.escape(c['who']), inline(c['where']), inline(c['original']), inline(c['text']))
        for c in sec.get('comments', []))
    body = (
        '%(nav)s<article class="essay"><h1>%(name)s · %(title)s</h1>'
        '<p class="incipit" lang="ja">%(incipit)s</p>%(translation)s'
        '<details class="deeper"><summary>Dig deeper: original, literal translation, notes</summary>'
        '%(legend)s%(pairs)s<h2>Notes</h2><dl>%(notes)s</dl>%(comments)s</details></article>%(nav)s'
    ) % {
        'nav': nav, 'name': section_name(sec['number']), 'title': html.escape(sec['title']),
        'incipit': inline(incipit(sec['original'])),
        'translation': ''.join('<p>%s</p>' % inline(t) for t in sec['translation']),
        'legend': legend, 'pairs': pairs, 'notes': notes,
        'comments': '<h2>Later readers</h2>' + comments if comments else '',
    }
    return page('%s · %s' % (section_name(sec['number']), sec['title']), body, css='../style.css')


def render_index(secs):
    items = ''.join('<li><a href="%d.html"><span class="num">%s</span> <span lang="ja">%s</span> %s</a></li>' % (
        s['number'], section_name(s['number']), inline(incipit(s['original'])), html.escape(s['title']))
        for s in secs)
    body = ('<h1>Tsurezuregusa · Essays in Idleness</h1><p class="intro">Yoshida Kenkō, c. 1330.</p>'
            '<ul class="contents">%s</ul>' % items)
    return page('Tsurezuregusa · Essays in Idleness', body, css='../style.css')


def load_feed(path):
    return json.loads(Path(path).read_text('utf-8'))


def main():
    out = ROOT / 'site'
    out.mkdir(exist_ok=True)
    shutil.copy(ROOT / 'style.css', out / 'style.css')
    for path in sorted((ROOT / 'content').glob('*.json')):
        (out / (path.stem + '.html')).write_text(render_page(load_feed(path)), 'utf-8')
        print('wrote', out / (path.stem + '.html'))
    secs = sorted((load_feed(p) for p in (ROOT / 'content' / 'kenko').glob('*.json')), key=lambda s: s['number'])
    if secs:
        edition = sections((ROOT / 'sources' / 'tsurezuregusa-wikisource.txt').read_text('utf-8'), modern=False)
        (out / 'kenko').mkdir(exist_ok=True)
        nums = [s['number'] for s in secs]
        for i, sec in enumerate(secs):
            prev = nums[i - 1] if i else None
            nxt = nums[i + 1] if i + 1 < len(nums) else None
            (out / 'kenko' / ('%d.html' % sec['number'])).write_text(render_essay(
                sec, prev, nxt, align_old(sec['original'], edition_text(edition, sec['number']))), 'utf-8')
        (out / 'kenko' / 'index.html').write_text(render_index(secs), 'utf-8')
        print('wrote', len(secs), 'Kenkō sections to', out / 'kenko')


if __name__ == '__main__':
    main()
