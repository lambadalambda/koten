#!/usr/bin/env python3
"""Render content/*.json feeds into static HTML pages in site/."""
import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).parent
RUBY = re.compile(r'\{([^{}|]+)\|([^{}|]+)\}')


def inline(text):
    """Escape text; turn {base|reading} into <ruby> and newlines into <br>."""
    parts, pos = [], 0
    for m in RUBY.finditer(text):
        parts.append(_plain(text[pos:m.start()]))
        parts.append('<ruby>%s<rt>%s</rt></ruby>' % (html.escape(m[1]), html.escape(m[2])))
        pos = m.end()
    parts.append(_plain(text[pos:]))
    return '<br>'.join(''.join(parts).splitlines())


def _plain(text):
    if any(c in text for c in '{}|'):
        raise ValueError('Malformed ruby markup near: %r' % text)
    return html.escape(text, quote=False)


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
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>%s</title><link rel="stylesheet" href="style.css"></head><body><main>'
        '<h1>%s</h1><p class="intro">%s</p>\n%s\n'
        '<footer><h2>Sources</h2><ul>%s</ul></footer></main></body></html>\n'
    ) % (html.escape(feed['title']), html.escape(feed['title']), inline(feed['intro']), posts, sources)


def load_feed(path):
    return json.loads(Path(path).read_text('utf-8'))


def main():
    out = ROOT / 'site'
    out.mkdir(exist_ok=True)
    shutil.copy(ROOT / 'style.css', out / 'style.css')
    for path in sorted((ROOT / 'content').glob('*.json')):
        (out / (path.stem + '.html')).write_text(render_page(load_feed(path)), 'utf-8')
        print('wrote', out / (path.stem + '.html'))


if __name__ == '__main__':
    main()
