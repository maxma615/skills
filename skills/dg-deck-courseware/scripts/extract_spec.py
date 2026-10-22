#!/usr/bin/env python3
"""Reverse a dg-deck HTML back into a JSON spec (used to create examples/lesson-2-01.zh.json).
usage: extract_spec.py deck.html -o spec.json  [--footer TEXT]"""
import argparse, glob, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = {}
for p in glob.glob(os.path.join(ROOT, 'assets', 'icons', '*.svg')):
    src = open(p, encoding='utf-8').read()
    _svg = BeautifulSoup(src, 'html.parser').find('svg')
    ICONS[re.sub(r'\s', '', ''.join(str(c) for c in _svg.contents))] = os.path.basename(p)[:-4]


WS = '\ue000'


def inner(el):
    if el is None:
        return None
    s = el.decode_contents(formatter='minimal').replace(WS, ' ')
    s = re.sub(r'<em class="hl">(.*?)</em>', r'==\1==', s)
    s = re.sub(r'<code class="ic">(.*?)</code>', r'`\1`', s)
    return s


def text_of(el):  # code line plain text
    return el.get_text().replace(WS, ' ')


def icon_of(el):
    svg = el.find('svg')
    k = re.sub(r'\s', '', ''.join(str(c) for c in svg.contents))
    if k not in ICONS:
        sys.exit('unknown icon: ' + k)
    tone = [c[2:] for c in el['class'] if c.startswith('t-')][0]
    return ICONS[k], tone


def hdr(sec, s):
    eb = sec.select_one('.eyebrow')
    if eb is not None:
        if eb.svg: eb.svg.extract()
        s['eyebrow'] = inner(eb)
    h = sec.select_one('.h1, .cv-title, .cl-title, .sec-title')
    if h is not None:
        s['heading'] = inner(h)
    lead = sec.select_one('.lead, .cv-lead, .cl-lead')
    if lead is not None:
        s['lead'] = inner(lead)


def slide(sec):
    lay = sec['data-layout']
    s = {'layout': lay, 'title': sec['data-title']}
    notes = sec.select_one('aside.notes')
    if lay == 'section':
        s['num'] = inner(sec.select_one('.sec-num'))
        s['heading'] = inner(sec.select_one('.sec-title'))
        sub = sec.select_one('.sec-sub')
        if sub: s['sub'] = inner(sub)
    else:
        hdr(sec, s)
    if lay == 'cover':
        s['tags'] = [{'text': inner(p), 'dark': True} if 'dark' in p['class'] else inner(p) for p in sec.select('.cv-tags .pill')]
        hero = sec.select_one('.hero')
        if hero:
            s['hero'] = {'center': inner(hero.select_one('.hc b')), 'caption': inner(hero.select_one('.hc span')),
                         'nodes': [inner(n) for n in hero.select('.hn > div')]}
    elif lay == 'cards':
        g = sec.select_one('.grid')
        cols = int([c for c in g['class'] if c.startswith('cols-')][0][5:])
        s['cols'] = cols
        if 'cards-row' in g['class']: s['row'] = True
        s['cards'] = []
        for c in g.select(':scope > .card'):
            cd = {}
            if c.select_one('.num'): cd['num'] = inner(c.select_one('.num'))
            if c.select_one('.ico'): cd['icon'], cd['tone'] = icon_of(c.select_one('.ico'))
            cd['title'] = inner(c.h3)
            if c.p: cd['text'] = inner(c.p)
            if 'focus' in c['class']: cd['focus'] = True
            extra = ''.join(x.decode(formatter='minimal') if hasattr(x, 'decode') and not isinstance(x, NavigableString) else x.output_ready('minimal') for x in c.contents[[i for i, x in enumerate(c.contents) if x is c.p][0] + 1:]) if c.p else ''
            if extra: cd['extra_html'] = extra
            s['cards'].append(cd)
    elif lay == 'flow':
        s['steps'] = []
        for f in sec.select('.fs'):
            st = {'t': inner(f.select_one('.t')), 's': inner(f.select_one('.s'))}
            if 'on' in f['class']: st['on'] = True
            s['steps'].append(st)
    elif lay == 'table':
        def cl(c):
            h = inner(c)
            o = {'html': h}
            if c.get('class'): o['cls'] = ' '.join(c['class'])
            if c.get('colspan'): o['colspan'] = int(c['colspan'])
            if c.get('style'): o['style'] = c['style']
            return h if len(o) == 1 else o
        s['head'] = [cl(c) for c in sec.select('thead th')]
        rows = sec.select('tbody tr')
        if rows and rows[0].contents[0].name == 'th': s['row_header'] = True
        s['rows'] = [[cl(c) for c in r.find_all(['td', 'th'], recursive=False)] for r in rows]
    elif lay == 'bullets':
        if sec.select_one('.nlist'):
            s['variant'] = 'numbered'
            s['items'] = [inner(n.select_one('.t')) for n in sec.select('.nl')]
        else:
            s['variant'] = 'split'
            rev = {'mk-x': 'x', 'mk-check': 'check', 'mk-info': 'info', 'mk-note': 'note'}
            s['items'] = []
            for li in sec.select('.blist li'):
                mk, sp = li.find_all('span', recursive=False)
                kinds = [rev[c] for c in mk['class'] if c in rev]
                it = {'mark': kinds[0] if kinds else 'num', 'text': inner(sp)}
                if 'muted' in (li.get('class') or []): it['muted'] = True
                s['items'].append(it)
    elif lay == 'code':
        s['blocks'] = []
        for row in sec.select('.code-row'):
            b = {'label': inner(row.select_one('.tlab'))}
            host = inner(row.select_one('.thost'))
            if host != 'root@rdk: ~': b['host'] = host
            b['lines'] = []
            for ln in row.select('.ln'):
                o = {'text': text_of(ln)}
                if 'hlt' in ln['class']: o['hl'] = True
                if 'out' in ln['class']: o['out'] = True
                b['lines'].append(o['text'] if len(o) == 1 else o)
            nt = row.select_one('.note')
            if nt: b['note'] = {'k': inner(nt.select_one('.k')), 'p': inner(nt.p)}
            s['blocks'].append(b)
    elif lay == 'bars':
        rows = sec.select('.br')
        sp = rows[0].select_one('[data-count]')
        s['dec'], s['sep'] = int(sp['data-dec']), sp['data-sep'] == '1'
        s['unit'] = rows[0].select_one('.v').contents[-1].strip()
        s['rows'] = []
        for r in rows:
            v = r.select_one('[data-count]')['data-count']
            s['rows'].append({'label': inner(r.select_one('.l')), 'value': float(v) if '.' in v else int(v),
                              'hi': 'hi' in r['class']})
    elif lay == 'links':
        s['items'] = [{'k': inner(a.select_one('.k')), 'd': inner(a.select_one('.d')), 'url': a['href']} for a in sec.select('a.lk')]
    elif lay == 'closing':
        s['cards'] = []
        for c in sec.select('.cl-card'):
            ic, tone = icon_of(c.select_one('.ico'))
            s['cards'].append({'icon': ic, 'tone': tone, 'k': inner(c.select_one('.k')), 'd': inner(c.select_one('.d'))})
        s['full_logo'] = sec.select_one('img.full-logo') is not None
    if notes is not None:
        s['notes'] = inner(notes)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html'); ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    raw = open(a.html, encoding='utf-8').read()
    # bs4 collapses whitespace-only text nodes; protect them (matters for indented code lines)
    raw = re.sub(r'>( +)<', lambda m: '>' + WS * len(m.group(1)) + '<', raw)
    soup = BeautifulSoup(raw, 'html.parser')
    secs = soup.select('section.slide')
    tag = secs[0].select_one('.tag-tr').get_text()
    foot = next((x.select_one('.foot span') for x in secs if x.select_one('.foot')), None)
    footer = foot.contents[0].rstrip(' ·') if foot else ''
    spec = {'meta': {'title': soup.html['data-title'], 'lang': soup.html['lang'], 'mode': soup.html['data-mode'],
                     'tag': tag, 'footer': str(footer), 'theme': {}},
            'slides': [slide(x) for x in secs]}
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'{len(secs)} slides -> {a.out}')


if __name__ == '__main__':
    main()
