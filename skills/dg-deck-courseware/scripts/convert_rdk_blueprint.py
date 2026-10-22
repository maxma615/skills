#!/usr/bin/env python3
"""Convert a blueprint JSON from skills/rdk-course-slides-generator
(lesson Markdown -> blueprint -> HTML) into a dg-deck spec.

usage: convert_rdk_blueprint.py blueprint.json -o spec.json [--tag "RDK 小课堂 1-01"] [--footer "社区与生态"]
       [--chapter 2 --chapter-name "Model Zoo" --lesson 1 [--subtitle "…"] [--visual bpu|quant|img] [--highlight BPU]]
Then:  build.py spec.json -o deck.html

Series lessons: pass --chapter/--chapter-name/--lesson and slide 1 becomes a `series-cover` (the series cover
style; the platform thumbnail is then rendered from the same fields with render_cover.py --spec spec.json).
Its title is the blueprint cover title ([gradient] part = highlight); --subtitle is one short line.

Pattern mapping (blueprint -> dg-deck):
  cover -> cover | cards-3/4/6/8 -> cards (cols 3/4/3/4) | split-checklist, checklist -> bullets(split, ✓)
  split-timeline, timeline -> timeline(schedule)* | path-6, path -> flow (≤6 steps) | flow-5 -> flow
  code-highlight -> code (2 terminals per slide; more cards are split over several slides)
  resource-list, resources -> links | closing -> closing          (* = 重建版式, not in the original dg-deck file)
Markup: [gradient]x[/gradient] -> ==x== ; tint-1..6 -> orange/yellow/yellow/blue/grey/green (dg-deck has no purple tone).
"""
import argparse, json, re, sys

TINT = {'tint-1': 'orange', 'tint-2': 'yellow', 'tint-3': 'yellow', 'tint-4': 'blue', 'tint-5': 'grey', 'tint-6': 'green'}
CMD_START = re.compile(r'^(sudo|cd|ls|cat|echo|python3?|pip3?|bash|sh|git|ros2|source|export|hrt_|hrut_|hb_|apt|ssh|scp|wget|curl|\./|/|v4l2|i2c|gst|ffmpeg|make|cmake|chmod|tail|grep|dmesg|systemctl|srpi|rdk|ifconfig|ip |ping|top|htop|lsusb|mkdir|cp |mv |rm |docker|uname|free|df |du |nano|vim)')


def grad(s):
    return re.sub(r'\[gradient\](.*?)\[/gradient\]', r'==\1==', s or '')


def tone(c, k):
    return TINT.get(c.get('tint'), ['orange', 'blue', 'green', 'yellow'][k % 4])


def head(b, title_default):
    s = {'title': b.get('data_title') or re.sub(r'\[/?gradient\]', '', b.get('title', title_default)),
         'eyebrow': b.get('kicker', ''), 'heading': grad(b.get('title', ''))}
    if b.get('lead'):
        s['lead'] = b['lead']
    if b.get('notes'):
        s['notes'] = b['notes']
    return s


def vw(t):  # visual width in mono-char units at 26px (CJK glyph ≈ 1.65 mono cells)
    return sum(1.65 if ord(ch) > 0x2E80 else 1 for ch in t)


NARROW, WIDE = 57, 94


def wrap(item, limit):
    out_line = isinstance(item, dict)
    text = item['text'] if out_line else item
    if vw(text) <= limit:
        return [item]
    res, cur = [], ''
    if not out_line:   # command: break at spaces, shell continuation
        lead = ''
        for w in text.split(' '):
            cand = (cur + ' ' + w) if cur else w
            if vw(cand) + 2 > limit and cur.strip():
                res.append(cur + ' \\'); cur = '  ' + w
            else:
                cur = cand
        res.append(cur)
        return res
    for ch in text:
        if vw(cur + ch) > limit:
            res.append({'text': cur, 'out': True}); cur = ''
        cur += ch
    res.append({'text': cur, 'out': True})
    return res


def code_lines(code):
    out = []
    for ln in str(code).split('\n'):
        if not ln.strip():
            continue
        if ln.startswith('$ ') or ln.lstrip().startswith('#'):
            out.append(ln)
        elif CMD_START.match(ln.strip()):
            out.append('$ ' + ln)
        else:
            out.append({'text': ln, 'out': True})
    return out


def convert(bp, tag=None, footer=None):
    meta = bp.get('meta', {})
    title = meta.get('title', 'RDK 小课堂')
    lang = {'cn': 'zh-CN', 'zh': 'zh-CN', 'en': 'en'}.get(meta.get('lang', 'cn'), meta.get('lang'))
    if footer is None:
        footer = re.split(r'[：:｜|]', title)[-1].strip()
    out = {'meta': {'title': title, 'lang': lang, 'tag': tag or 'RDK 小课堂', 'footer': footer}, 'slides': []}
    if meta.get('logo_key') == 'logo-en' or lang == 'en':
        out['meta']['logo_full'] = 'd-robotics-logo-full-en.png'
    warn = []
    for i, b in enumerate(bp['slides'], 1):
        p = b.get('pattern')
        if p == 'cover':
            s = {'layout': 'cover', **head(b, 'Cover')}
            s['tags'] = list(b.get('tags', []))
            plain = re.sub(r'\[/?gradient\]', '', b.get('title', ''))
            if (b.get('hero_nodes') or b.get('hero_center')) and vw(plain) > 11:
                warn.append(f'slide {i} (cover): title too long for the 920px column next to the hero — hero dropped (cv-left full)')
            elif b.get('hero_nodes') or b.get('hero_center'):
                hc = b.get('hero_center', {'strong': 'RDK', 'sub': ''})
                s['hero'] = {'center': hc.get('strong', 'RDK'), 'caption': hc.get('sub', ''), 'nodes': b.get('hero_nodes', [])}
            out['slides'].append(s)
        elif p in ('cards-3', 'cards-4', 'cards-6', 'cards-8'):
            n = len(b.get('cards', []))
            cols = {'cards-3': 3, 'cards-4': 4, 'cards-6': 3, 'cards-8': 4}[p]
            s = {'layout': 'cards', **head(b, 'Cards'), 'cols': cols,
                 'cards': [{'icon': c.get('icon', 'zap'), 'tone': tone(c, k), 'title': c.get('title', ''), 'text': c.get('body', '')}
                           if isinstance(c, dict) else {'num': f'{k + 1:02d}', 'title': c}
                           for k, c in enumerate(b.get('cards', []))]}
            if n > cols:
                s['dense'] = True          # extension: compact 2-row grid

            out['slides'].append(s)
        elif p in ('split-checklist', 'checklist'):
            items = b.get('items', [])
            if not items:
                warn.append(f'slide {i} ({p}): blueprint has no items — rendered as heading + lead only')
            out['slides'].append({'layout': 'bullets', 'variant': 'split', **head(b, 'Checklist'),
                                  'items': [{'mark': 'check', 'text': t} for t in items]})
        elif p in ('split-timeline', 'timeline'):
            steps = b.get('steps', [])
            items = [{'tm': st.get('badge', f'Step {k + 1}'), 't': st.get('body', st.get('title', ''))} if isinstance(st, dict)
                     else {'tm': f'Step {k + 1}', 't': st} for k, st in enumerate(steps)]
            out['slides'].append({'layout': 'timeline', 'variant': 'schedule', **head(b, 'Timeline'), 'items': items})
        elif p in ('path-6', 'path', 'flow-5'):
            steps = b.get('steps', [])
            fs = []
            for k, st in enumerate(steps):
                if isinstance(st, dict):
                    f = {'t': st.get('title', ''), 's': st.get('sub', st.get('body', ''))}
                    if st.get('no'):
                        f['num'] = st['no']
                else:
                    f = {'t': st}
                fs.append(f)
            if len(fs) > 6:
                warn.append(f'slide {i} ({p}): {len(fs)} steps (>6) — flow gets cramped')
            out['slides'].append({'layout': 'flow', **head(b, 'Flow'), 'steps': fs})
        elif p == 'code-highlight':
            cards = b.get('cards', [])
            chunks = [cards[k:k + 2] for k in range(0, len(cards), 2)] or [[]]
            for j, ch in enumerate(chunks):
                s = {'layout': 'code', **head(b, 'Code')}
                if len(chunks) > 1:
                    s['title'] += f' ({j + 1}/{len(chunks)})'
                    if j:
                        s.pop('notes', None)
                s['blocks'] = []
                for c in ch:
                    lines = code_lines(c.get('code', ''))
                    blk = {'label': c.get('title', '')}
                    if max((vw(x['text'] if isinstance(x, dict) else x) for x in lines), default=0) > NARROW:
                        blk['wide'] = True        # extension: note goes under the terminal, terminal spans full width
                        lines = [y for x in lines for y in wrap(x, WIDE)]
                    blk['lines'] = lines
                    if c.get('note'):
                        blk['note'] = {'k': '要点' if lang == 'zh-CN' else 'Note', 'p': c['note']}
                    s['blocks'].append(blk)
                nlines = sum(len(b['lines']) for b in s['blocks']) + sum(2 for b in s['blocks'] if b.get('wide'))
                if nlines > 6:
                    s['dense'] = True
                out['slides'].append(s)
            if len(chunks) > 1:
                warn.append(f'slide {i} (code-highlight): {len(cards)} commands split over {len(chunks)} code slides')
        elif p in ('resource-list', 'resources'):
            out['slides'].append({'layout': 'links', **head(b, 'Resources'),
                                  'items': [{'k': r.get('name', ''), 'd': r.get('desc', ''), 'url': r.get('href', '#')}
                                            for r in b.get('resources', [])]})
        elif p == 'closing':
            out['slides'].append({'layout': 'closing', **head(b, 'Closing'),
                                  'cards': [{'icon': c.get('icon', 'zap'), 'tone': tone(c, k), 'k': c.get('title', ''), 'd': c.get('body', '')}
                                            if isinstance(c, dict) else {'icon': 'zap', 'tone': tone({}, k), 'k': c}
                                            for k, c in enumerate(b.get('cards', []))]})
        else:
            warn.append(f'slide {i}: unknown pattern "{p}" skipped')
    return out, warn


def series_cover(spec, bp, a):
    """Replace (or insert) slide 1 with a series-cover built from the blueprint cover + CLI fields."""
    b = next((x for x in bp['slides'] if x.get('pattern') == 'cover'), {})
    raw = a.cover_title or b.get('title', '')
    m = re.search(r'\[gradient\](.*?)\[/gradient\]', raw)
    title = re.sub(r'\[/?gradient\]', '', raw).strip()
    if not title:
        sys.exit('series cover: no title (blueprint cover has none; pass --cover-title)')
    s = {'layout': 'series-cover', 'chapter': a.chapter, 'chapter_name': a.chapter_name, 'lesson': a.lesson,
         'title': title}
    hl = a.highlight or (m.group(1) if m else None)
    if hl:
        s['highlight'] = hl
    if a.subtitle:                        # one short line; blueprint leads are usually too long for it
        s['subtitle'] = a.subtitle
    s['visual'] = a.visual
    if b.get('notes'):
        s['notes'] = b['notes']
    sl = spec['slides']
    if sl and sl[0]['layout'] == 'cover':
        sl[0] = s
    else:
        sl.insert(0, s)
    spec['meta'].pop('title', None)        # build.py derives the series title from the cover
    spec['meta']['tag'] = a.tag or ('RDK Classroom' if spec['meta'].get('lang') == 'en' else 'RDK 小课堂') + f' {a.chapter}-{a.lesson:02d}'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('blueprint'); ap.add_argument('-o', '--out', required=True)
    ap.add_argument('--tag'); ap.add_argument('--footer')
    g = ap.add_argument_group('series cover (slide 1)')
    g.add_argument('--chapter', type=int); g.add_argument('--chapter-name'); g.add_argument('--lesson', type=int)
    g.add_argument('--cover-title'); g.add_argument('--highlight'); g.add_argument('--subtitle')
    g.add_argument('--visual', default='bpu', help='bpu | quant | image path | "" (default bpu)')
    a = ap.parse_args()
    bp = json.load(open(a.blueprint, encoding='utf-8'))
    spec, warn = convert(bp, a.tag, a.footer)
    sc = [a.chapter is not None, bool(a.chapter_name), a.lesson is not None]
    if any(sc) and not all(sc):
        sys.exit('series cover needs all of --chapter, --chapter-name, --lesson')
    if all(sc):
        series_cover(spec, bp, a)
        warn = [w for w in warn if '(cover)' not in w]
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False, indent=2); f.write('\n')
    print(f'{a.blueprint}: {len(spec["slides"])} dg-deck slides -> {a.out}')
    for w in warn:
        print('  ! ' + w)


if __name__ == '__main__':
    main()
