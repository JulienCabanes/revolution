#!/usr/bin/env python3
"""Build the page from the story sources.

    python3 tools/build.py

story/<lang>/book.json describes one edition; its chapters are the
story/<lang>/*.txt files, read in file name order. The cast (story/cast.json)
is shared by every edition. The format of the chapter files is described in
README.md. The output is a single self-contained HTML file.
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StoryError(Exception):
    pass


def load_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise StoryError('%s: %s' % (os.path.relpath(path, ROOT), e))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- inline text

NBSP, NNBSP = ' ', ' '
TYPOGRAPHY = None  # set per edition from book.json "typography"

BOLD = re.compile(r'(?<!\*)\*\*(?!\*)(\S(?:.*?\S)?)(?<!\*)\*\*(?!\*)')
ITALIC = re.compile(r'(?<![\w*])\*(?!\*)(\S(?:.*?\S)?)(?<!\*)\*(?![\w*])')


def typo(text):
    """French typography: curly apostrophes, non-breaking spaces."""
    if TYPOGRAPHY != 'fr':
        return text
    s = text.replace("'", '’')
    s = re.sub(r' ([?!;»])', NNBSP + r'\1', s)
    s = s.replace('« ', '«' + NNBSP)
    s = re.sub(r' :(?=\s|$|\*)', NBSP + ':', s)
    s = re.sub(r'(\d) (?=(h|min|m|s|%|€)\b|%|€)', r'\1' + NBSP, s)
    s = re.sub(r'(?<=\d) (?=\d{3}\b)', NBSP, s)
    return s


def inline(text):
    """Escape text, then apply **bold** and *italic*."""
    s = esc(typo(text))
    s = BOLD.sub(r'<strong>\1</strong>', s)
    return ITALIC.sub(r'<em>\1</em>', s)


# An emoji-only message (up to three) is shown big, without a bubble.
EMOJI_ONLY = re.compile(r'^(?:[\U0001F000-\U0001FAFF☀-➿️‍\U0001F3FB-\U0001F3FF]\s*){1,3}$')

ATTACHMENTS = {
    'lien': ('🔗', 'Lien'),
    'photo': ('🖼️', 'Photo'),
    'vidéo': ('🎬', 'Vidéo'),
    "capture d'écran": ('🖼️', "Capture d'écran"),
    'vocal': ('🎤', 'Message vocal'),
    'document': ('📄', 'Document'),
}


def attachment(label):
    key = label.split(' ')[0] if label.split(' ')[0] in ('vocal',) else label
    icon, name = ATTACHMENTS.get(key.lower(), ('📎', label))
    extra = label[len(key):].strip() if key != label else ''
    text = name + (' · ' + extra if extra else '')
    return '<div class="att"><span class="ai">%s</span>%s</div>' % (icon, inline(text))


# ---------------------------------------------------------------- the edition

class Edition:
    def __init__(self, book_path, cast):
        self.book = load_json(book_path)
        self.dir = os.path.dirname(book_path)
        global TYPOGRAPHY
        TYPOGRAPHY = self.book.get('typography')
        self.cast = cast
        self.out = []
        self.groups = []          # successive names of the group
        self.last_sender = None   # to merge the avatar of consecutive messages
        self.chapters = []
        self.stats = dict(messages=0, articles=0)

    def need_cast(self, cid, where):
        if cid not in self.cast:
            raise StoryError('%s: unknown character "%s" (known: %s)'
                             % (where, cid, ', '.join(sorted(self.cast))))
        return self.cast[cid]

    # -- blocks

    def directive(self, line, where):
        m = re.match(r'#\s+(.*?)(?:\s*\|\s*(.*?))?(?:\s*\{#([\w-]+)\})?\s*$', line)
        if m:
            title, sub, anchor = m.groups()
            anchor = anchor or 'c%d' % (len(self.chapters) + 1)
            self.chapters.append((anchor, title, sub))
            self.out.append('<section class="chapter" id="%s"><div class="ct">%s</div>%s</section>'
                            % (attr(anchor), inline(title),
                               '<div class="cs">%s</div>' % inline(sub) if sub else ''))
            self.last_sender = None
            return
        m = re.match(r'---\s*(.*)$', line)
        if m:
            self.out.append('<div class="day"><span>%s</span></div>' % inline(m.group(1)))
            self.last_sender = None
            return
        m = re.match(r'\[(\w+)\]\s*(.*)$', line)
        if not m:
            raise StoryError('%s: cannot read "%s"' % (where, line))
        kind, arg = m.groups()
        if kind == 'group':
            self.groups.append(arg)
            if len(self.groups) > 1:
                self.out.append('<div class="mark" data-group="%d"></div>' % (len(self.groups) - 1))
        elif kind == 'event':
            self.out.append('<div class="event"><span>%s</span></div>' % inline(arg))
            self.last_sender = None
        elif kind == 'interlude':
            self.out.append('<div class="interlude">%s</div>' % inline(arg))
            self.last_sender = None
        elif kind == 'spacer':
            self.out.append('<div class="spacer"></div>')
            self.last_sender = None
        else:
            raise StoryError('%s: unknown directive [%s]' % (where, kind))

    def article(self, lines, where):
        source = re.match(r'\[article\]\s*(.*)$', lines[0]).group(1)
        if len(lines) < 2:
            raise StoryError('%s: an article needs a title line' % where)
        body = ''.join('<p>%s</p>' % inline(l) for l in lines[2:])
        self.out.append('<article class="press"><div class="src">%s</div><h2>%s</h2>%s</article>'
                        % (inline(source), inline(lines[1]), body))
        self.last_sender = None
        self.stats['articles'] += 1

    def message(self, lines, where):
        m = re.match(r'(\w+)\s+(\d{1,2}):(\d{2})((?:\s+\w+)*)$', lines[0])
        if not m:
            raise StoryError('%s: expected "character HH:MM", got "%s"' % (where, lines[0]))
        cid, h, mi, opts = m.groups()
        who = self.need_cast(cid, where)
        time = self.book['ui']['time'].format(h=h, m=mi)
        text = lines[1:]
        if not text:
            raise StoryError('%s: empty message' % where)

        parts, quote = [], []

        def flush_quote():
            if quote:
                parts.append('<blockquote>%s</blockquote>' % '<br>'.join(quote))
                quote.clear()

        for l in text:
            if l.startswith('> ') or l == '>':
                quote.append(inline(l[2:]))
                continue
            flush_quote()
            a = re.match(r'^\[([^\]]+)\]$', l)
            parts.append(attachment(a.group(1)) if a else '<div class="l">%s</div>' % inline(l))
        flush_quote()

        big = 'big' in opts.split() or (len(text) == 1 and EMOJI_ONLY.match(text[0]))
        first = self.last_sender != cid
        self.last_sender = cid
        color = who['color']
        avatar = ('<span class="av" style="background:%s">%s</span>' % (attr(color), esc(who['name'][:1].upper()))
                  if first else '<span class="av none"></span>')
        name = '<div class="who" style="color:%s">%s</div>' % (attr(color), esc(who['name'])) if first else ''
        cls = 'msg' + (' first' if first else '') + (' big' if big else '')
        self.out.append('<div class="%s">%s<div class="bubble">%s<div class="txt">%s</div><span class="time">%s</span></div></div>'
                        % (cls, avatar, name, ''.join(parts), esc(time)))
        self.stats['messages'] += 1

    def chapter_file(self, path):
        name = os.path.relpath(path, ROOT)
        text = read(path)
        lineno = 1
        for block in re.split(r'(\n\s*\n)', text):
            if not block.strip() or block.isspace():
                lineno += block.count('\n')
                continue
            raw = block.split('\n')
            lines = [l.rstrip() for l in raw if l.strip()]
            where = '%s:%d' % (name, lineno + next(i for i, l in enumerate(raw) if l.strip()))
            lineno += block.count('\n')
            if lines[0].startswith('[article]'):
                self.article(lines, where)
            elif re.match(r'#\s|---|\[', lines[0]):
                for l in lines:
                    self.directive(l, where)
            else:
                self.message(lines, where)

    def build(self):
        files = sorted(glob.glob(os.path.join(self.dir, '*.txt')))
        if not files:
            raise StoryError('no chapter in %s' % os.path.relpath(self.dir, ROOT))
        for f in files:
            self.chapter_file(f)
        if not self.groups:
            raise StoryError('the first chapter must name the group with [group] …')

        members = self.book['group']['members']
        for m in members:
            self.need_cast(m, 'book.json: group')
        tpl = os.path.join(ROOT, 'templates')
        avatars = ''.join('<span class="av" style="background:%s">%s</span>'
                          % (attr(self.cast[m]['color']), esc(self.cast[m]['name'][:1])) for m in members)
        page = read(os.path.join(tpl, 'page.html'))
        values = {
            'lang': attr(self.book['lang']),
            'page_title': esc(self.book['page_title']),
            'style': read(os.path.join(tpl, 'style.css')),
            'script': read(os.path.join(tpl, 'app.js')),
            'group': inline(self.groups[0]),
            'groups': json.dumps([inline(g) for g in self.groups], ensure_ascii=False),
            'members': esc(', '.join(self.cast[m]['name'] for m in members)),
            'avatars': avatars,
            'title': inline(self.book['title']),
            'intro': ''.join('<p>%s</p>' % inline(p) for p in self.book.get('intro', [])),
            'feed': '\n'.join(self.out),
            'epilogue': inline(self.book.get('epilogue', '')),
        }
        for k, v in values.items():
            page = page.replace('{{%s}}' % k, v)
        left = re.findall(r'\{\{\w+\}\}', page)
        if left:
            raise StoryError('templates/page.html: unfilled %s' % ', '.join(left))
        out = os.path.join(ROOT, self.book['output'])
        with open(out, 'w', encoding='utf-8') as f:
            f.write(page)
        return out


def main():
    try:
        cast = load_json(os.path.join(ROOT, 'story', 'cast.json'))
        for cid, c in cast.items():
            if 'name' not in c or 'color' not in c:
                raise StoryError('story/cast.json: "%s" needs a name and a color' % cid)
        for book in sorted(glob.glob(os.path.join(ROOT, 'story', '*', 'book.json'))):
            ed = Edition(book, cast)
            out = ed.build()
            print('%s: %d messages, %d articles' % (os.path.relpath(out, ROOT),
                                                    ed.stats['messages'], ed.stats['articles']))
    except StoryError as e:
        sys.exit('error: %s' % e)


if __name__ == '__main__':
    main()
