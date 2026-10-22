#!/usr/bin/env python3
"""dg-deck build: JSON spec -> single self-contained offline HTML deck.

Recovered from lesson-2-01.zh.html (generator meta "dg-deck").  The CSS / JS
runtime / page skeleton are the original bytes (assets/templates/); slide markup and
animation-stagger timings are re-implemented here to match the original.

usage: build.py spec.json [-o out.html] [--resubset] [--no-subset-check]
"""
import argparse, base64, html, io, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'assets', 'templates')
ASSETS = os.path.join(ROOT, 'assets')


def rd(p, mode='r'):
    with open(p, mode, **({} if 'b' in mode else {'encoding': 'utf-8'})) as f:
        return f.read()


def b64(path):
    return base64.b64encode(rd(path, 'rb')).decode('ascii')


def esc(s):          # text node escape (code lines, urls)
    return html.escape(str(s), quote=False)


def attr(s):         # attribute escape
    return html.escape(str(s), quote=True)


def inl(s):
    """Inline-HTML field.  Shorthands: ==x== -> <em class="hl">x</em>, `x` -> <code class="ic">x</code>.
    Everything else is passed through as HTML (escape & < > yourself)."""
    if s is None:
        return ''
    s = str(s)
    s = re.sub(r'==(.+?)==', r'<em class="hl">\1</em>', s)
    s = re.sub(r'`(.+?)`', r'<code class="ic">\1</code>', s)
    return s


def d(ms):
    return f' style="--d:{ms};"'


# ---------------------------------------------------------------- icons
SVG_OPEN = ('<svg class="" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
            'stroke-linecap="round" stroke-linejoin="round">')
_icon_cache = {}


ICON_ALIASES = {'brain': 'network', 'list-check': 'list-checks', 'gradcap': 'graduation-cap'}  # names used by rdk-course-slides-generator


def icon(name):
    name = ICON_ALIASES.get(name, name)
    if name not in _icon_cache:
        p = os.path.join(ASSETS, 'icons', name + '.svg')
        if not os.path.exists(p):
            sys.exit(f'unknown icon "{name}" (see assets/icons/)')
        src = rd(p)
        inner = src[src.index('>') + 1:src.rindex('</svg>')]
        _icon_cache[name] = SVG_OPEN + inner + '</svg>'
    return _icon_cache[name]


SPARKLE = None


def sparkle():
    global SPARKLE
    if SPARKLE is None:
        SPARKLE = rd(os.path.join(TPL, 'sparkle.svg.html')).strip()
    return SPARKLE


# ---------------------------------------------------------------- chrome
BG = {
    'stage': '<div class="bg bg-stage"><div class="glow-a"></div><div class="glow-b"></div></div>',
    'white': '<div class="bg bg-white"></div><div class="blob"></div>',
    'dark': '<div class="bg bg-dark"></div>',          # CSS exists in theme; not used in the 2-01 deck
}


def header(s, lead_d=270):
    """eyebrow + h1 + optional lead; returns (html, content-start delay)."""
    h = f'<div class="eyebrow" data-a="fade"{d(120)}>{inl(s.get("eyebrow", ""))}</div>'
    h += f'<h2 class="h1" data-a="rise"{d(180)}>{inl(s.get("heading", ""))}</h2>'
    if s.get('lead'):
        h += f'<p class="lead" data-a="rise"{d(lead_d)}>{inl(s["lead"])}</p>'
        return h, 420
    return h, 330


def body(s, content, top=False):
    h, _ = header(s)
    return f'<div class="body">{h}<div class="content{" top" if top else ""}">{content}</div></div>'


def start(s):
    return 420 if s.get('lead') else 330


# ---------------------------------------------------------------- layouts
def L_cover(s, ctx):
    hero = s.get('hero')
    out = f'<div class="cv-left{"" if hero else " full"}">'
    out += f'<div class="eyebrow lg" data-a="fade"{d(120)}>{sparkle()}{inl(s.get("eyebrow", ""))}</div>'
    out += f'<h1 class="cv-title" data-a="rise"{d(220)}>{inl(s.get("heading", ""))}</h1>'
    if s.get('lead'):
        out += f'<p class="cv-lead" data-a="rise"{d(330)}>{inl(s["lead"])}</p>'
    if s.get('tags'):
        pills = ''
        for t in s['tags']:
            t = t if isinstance(t, dict) else {'text': t}
            pills += f'<span class="pill{" dark" if t.get("dark") else ""}">{inl(t["text"])}</span>'
        out += f'<div class="cv-tags" data-a="rise"{d(430)}>{pills}</div>'
    out += '</div>'
    if hero:
        nodes = hero.get('nodes', [])
        n = len(nodes)
        last = 520 + 90 * n
        out += '<div class="hero">'
        out += (f'<svg class="ring" viewBox="0 0 600 600" data-a="fade"{d(last)}><circle cx="300" cy="300" r="250" '
                'fill="none" stroke="#FF5A00" stroke-opacity=".35" stroke-width="3" stroke-dasharray="4 14" '
                'stroke-linecap="round"/></svg>')
        out += (f'<div class="hc" data-a="pop"{d(last)}><b>{inl(hero.get("center", ""))}</b>'
                f'<span>{inl(hero.get("caption", ""))}</span></div>')
        for k, node in enumerate(nodes):      # evenly on r=250, clockwise from 12 o'clock
            a = -math.pi / 2 + 2 * math.pi * k / n
            x, y = round(300 + 250 * math.cos(a)), round(300 + 250 * math.sin(a))
            out += f'<div class="hn" style="left:{x}px;top:{y}px"><div data-a="pop"{d(520 + 90 * k)}>{inl(node)}</div></div>'
        out += '</div>'
    return out


def L_section(s, ctx):
    out = '<div class="sec-left">'
    out += f'<div class="sec-num" data-a="num"{d(120)}>{inl(s["num"])}</div>'
    out += f'<div class="rule" data-a="draw"{d(280)}></div>'
    out += f'<div class="sec-title" data-a="rise"{d(420)}>{inl(s.get("heading", ""))}</div>'
    if s.get('sub'):
        out += f'<div class="sec-sub" data-a="rise"{d(530)}>{inl(s["sub"])}</div>'
    out += '</div>'
    toc = s.get('toc', ctx['toc'])
    if toc:
        out += '<div class="sec-toc">'
        for k, item in enumerate(toc):
            on = (k == ctx['section_index']) if 'toc_on' not in s else (k == s['toc_on'])
            out += f'<div class="{"on" if on else ""}" data-a="left"{d(120 + 70 * k)}>{inl(item)}</div>'
        out += '</div>'
    return out


def L_cards(s, ctx):
    cards = s['cards']
    cols = s.get('cols', len(cards))
    t0 = start(s)
    if s.get('dense'):
        ctx['ext'] = True
    g = f'<div class="grid cols-{cols}{" cards-row" if s.get("row") else ""}{" dense" if s.get("dense") else ""}">'
    for k, c in enumerate(cards):
        g += f'<div class="card{" focus" if c.get("focus") else ""}" data-a="rise"{d(t0 + 90 * k)}>'
        if c.get('num') is not None:
            g += f'<div class="num">{inl(c["num"])}</div>'
        if c.get('icon'):
            g += f'<div class="ico t-{c.get("tone", "orange")}">{icon(c["icon"])}</div>'
        g += f'<h3>{inl(c.get("title", ""))}</h3>'
        if c.get('text'):
            g += f'<p>{inl(c["text"])}</p>'
        g += c.get('extra_html', '')
        g += '</div>'
    g += '</div>'
    return body(s, g)


def L_flow(s, ctx):
    steps = s['steps']
    t0 = start(s)
    f = f'<div class="flow" style="grid-template-columns:repeat({len(steps)},1fr)">'
    f += f'<div class="track" data-a="draw"{d(t0)}></div>'
    for k, st in enumerate(steps):
        f += (f'<div class="fs{" on" if st.get("on") else ""}" data-a="rise"{d(t0 + 110 * k)}>'
              f'<div class="c">{inl(st.get("num", f"{k + 1:02d}"))}</div><div class="t">{inl(st["t"])}</div>')
        if st.get('s'):
            f += f'<div class="s">{inl(st["s"])}</div>'
        f += '</div>'
    f += '</div>'
    return body(s, f)


def cell(c, tag):
    if not isinstance(c, dict):
        c = {'html': c}
    a = ''
    if c.get('cls'):
        a += f' class="{c["cls"]}"'
    if c.get('colspan'):
        a += f' colspan="{c["colspan"]}"'
    if c.get('style'):
        a += f' style="{c["style"]}"'
    tag = 'th' if c.get('th') else tag
    return f'<{tag}{a}>{inl(c.get("html", ""))}</{tag}>'


def L_table(s, ctx):
    rows = s['rows']
    t0 = start(s)
    t = '<table class="tb">'
    if s.get('head'):
        t += f'<thead><tr data-a="fade"{d(t0 + 70 * len(rows))}>' + ''.join(cell(c, 'th') for c in s['head']) + '</tr></thead>'
    t += '<tbody>'
    for k, r in enumerate(rows):
        t += f'<tr data-a="rise"{d(t0 + 70 * k)}>'
        for j, c in enumerate(r):
            t += cell(c, 'th' if (j == 0 and s.get('row_header')) else 'td')
        t += '</tr>'
    t += '</tbody></table>'
    if s.get('note'):
        t += f'<p class="tnote" data-a="fade"{d(t0 + 70 * len(rows) + 70)}>{inl(s["note"])}</p>'   # .tnote CSS exists; not used in 2-01
    return body(s, t)


MARKS = {'x': ('mk mk-x', '✕'), 'check': ('mk mk-check', '✓'), 'info': ('mk mk-info', '→'),
         'note': ('mk mk-note', '!'), 'num': ('mk', None)}


def L_bullets(s, ctx):
    items = s['items']
    if s.get('variant', 'split') == 'numbered':
        t0 = start(s)
        c = '<div class="nlist">'
        for k, it in enumerate(items):
            it = it if isinstance(it, dict) else {'text': it}
            c += (f'<div class="nl" data-a="left"{d(t0 + 80 * k)}><div class="n">{inl(it.get("num", f"{k + 1:02d}"))}</div>'
                  f'<div class="t">{inl(it["text"])}</div></div>')
        c += '</div>'
        return body(s, c)
    # split: heading block left (700px), white list card right
    out = '<div class="split"><div>'
    out += f'<div class="eyebrow" data-a="fade"{d(120)}>{inl(s.get("eyebrow", ""))}</div>'
    out += f'<h2 class="h1" data-a="rise"{d(180)}>{inl(s.get("heading", ""))}</h2>'
    out += f'<div class="rule" data-a="draw"{d(270)}></div>'
    t0 = 360
    if s.get('lead'):
        out += f'<p class="lead" data-a="rise"{d(360)}>{inl(s["lead"])}</p>'
        t0 = 450
    if not items:
        return out + '</div></div>'
    out += '</div><ul class="blist">'
    for k, it in enumerate(items):
        it = it if isinstance(it, dict) else {'text': it}
        cls, glyph = MARKS[it.get('mark', 'num')]
        glyph = it.get('glyph', glyph if glyph is not None else f'{k + 1}')
        out += (f'<li class="{"muted" if it.get("muted") else ""}" data-a="left"{d(t0 + 70 * k)}>'
                f'<span class="{cls}">{inl(glyph)}</span><span>{inl(it["text"])}</span></li>')
    out += '</ul></div>'
    return out


TOK = re.compile(r"""(?P<st>'[^']*'|"[^"]*")|(?P<ph><[^<>\n]+>)|(?P<op>(?<=\s)--?[A-Za-z][\w-]*)|(?P<cm>(?:(?<=\s)|^)#.*$)""")


def highlight(text):
    """Terminal line -> HTML.  '$ ' prompt, -flags, 'strings', <placeholders>, # comments."""
    out = ''
    if text.startswith('$ '):
        out, text = '<span class="pr">$ </span>', text[2:]
    pos = 0
    for m in TOK.finditer(text):
        out += esc(text[pos:m.start()])
        out += f'<span class="{m.lastgroup}">{esc(m.group(0))}</span>'
        pos = m.end()
    return out + esc(text[pos:])


def L_code(s, ctx):
    t = start(s)
    rows = ''
    for blk in s['blocks']:
        term_d = t
        lines_html, ln_d = '', term_d + 160
        for ln in blk['lines']:
            ln = ln if isinstance(ln, dict) else {'text': ln}
            text = ln['text']
            steps = len(text)
            tdur = min(600, 100 + 12 * steps)
            cls = 'ln' + (' hlt' if ln.get('hl') else '') + (' out' if ln.get('out') else '')
            st = (f'--hd:{ln_d + tdur + 210};' if ln.get('hl') else '') + f'--d:{ln_d};--steps:{steps};--tdur:{tdur}ms'
            body_html = ln['html'] if 'html' in ln else (esc(text) if ln.get('out') else highlight(text))
            lines_html += f'<div class="{cls}" data-a="type" style="{st}">{body_html}</div>'
            last_d, last_dur = ln_d, tdur
            ln_d = ln_d + tdur + 60
        term = (f'<div class="term" data-a="pop"{d(term_d)}><div class="tbar"><span class="dot" style="background:#EA4335"></span>'
                '<span class="dot" style="background:#FBBC04"></span><span class="dot" style="background:#34A853"></span>'
                f'<span class="tlab">{inl(blk.get("label", ""))}</span><span class="thost">{inl(blk.get("host", "root@rdk: ~"))}</span></div>'
                f'<div class="tbody">{lines_html}</div></div>')
        note = blk.get('note')
        if note:
            term += (f'<div class="note" data-a="left"{d(term_d + 300)}><div class="k">{inl(note.get("k", "要点"))}</div>'
                     f'<p>{inl(note["p"])}</p></div>')
        if blk.get('wide') and note:
            ctx['ext'] = True
        rows += f'<div class="code-row{" wide" if (blk.get("wide") or not note) else ""}">{term}</div>'
        t = last_d + last_dur - 140
    if s.get('dense'):
        ctx['ext'] = True
    return body(s, f'<div class="code-rows{" dense" if s.get("dense") else ""}">{rows}</div>')


def L_bars(s, ctx):
    rows = s['rows']
    dec, sep = int(s.get('dec', 0)), bool(s.get('sep', False))
    unit = s.get('unit', '')
    mx = max(float(r['value']) for r in rows) or 1
    hi_default = max(range(len(rows)), key=lambda k: float(rows[k]['value']))
    t0 = start(s)
    b = '<div class="bars">'
    for k, r in enumerate(rows):
        v = r['value']
        hi = r.get('hi', k == hi_default)
        rd_ = t0 + 110 * k
        shown = f'{float(v):,.{dec}f}' if sep else f'{float(v):.{dec}f}'
        b += (f'<div class="br{" hi" if hi else ""}" data-a="rise"{d(rd_)}><div class="l">{inl(r["label"])}</div>'
              f'<div class="tr"><div class="b" style="width:{float(v) / mx * 100:.2f}%;--d:{rd_ + 100}" data-a="bar"></div></div>'
              f'<div class="v"><b><span data-count="{v}" data-dec="{dec}" data-sep="{1 if sep else 0}" data-delay="{rd_ + 100}">{shown}</span></b>'
              f'{(" " + inl(r.get("unit", unit))) if r.get("unit", unit) else ""}</div></div>')
    b += '</div>'
    return body(s, b)


def L_links(s, ctx):
    t0 = start(s)
    c = '<div class="links">'
    for k, it in enumerate(s['items']):
        c += (f'<a class="lk" href="{attr(it["url"])}" target="_blank" rel="noopener" data-a="left"{d(t0 + 60 * k)}>'
              f'<div class="k">{inl(it["k"])}</div><div class="d">{inl(it.get("d", ""))}</div>'
              f'<div class="u">{esc(it.get("show_url", it["url"]))}</div></a>')
    c += '</div>'
    return body(s, c, top=True)


def L_closing(s, ctx):
    out = '<div class="cl">'
    out += f'<div class="eyebrow lg" data-a="fade"{d(120)}>{sparkle()}{inl(s.get("eyebrow", ""))}</div>'
    out += f'<h2 class="cl-title" data-a="rise"{d(220)}>{inl(s.get("heading", ""))}</h2>'
    if s.get('lead'):
        out += f'<p class="cl-lead" data-a="rise"{d(330)}>{inl(s["lead"])}</p>'
    cards = s.get('cards', [])
    last = 330
    if cards:
        out += f'<div class="cl-cards" style="grid-template-columns:repeat({s.get("cols", len(cards))},1fr)">'
        for k, c in enumerate(cards):
            last = 440 + 90 * k
            out += f'<div class="cl-card" data-a="rise"{d(last)}>'
            if c.get('icon'):
                out += f'<div class="ico t-{c.get("tone", "orange")}">{icon(c["icon"])}</div>'
            out += f'<div class="k">{inl(c.get("k", ""))}</div><div class="d">{inl(c.get("d", ""))}</div>'
            if c.get('u'):
                out += f'<div class="u">{inl(c["u"])}</div>'   # .cl-card .u CSS exists; not used in 2-01
            out += '</div>'
        out += '</div>'
    out += '</div>'
    if s.get('full_logo', True):
        out += (f'<img class="full-logo" src="data:image/png;base64,{ctx["logo_full"]}" alt="D-Robotics" '
                f'data-a="fade"{d(last + 90)}>')
    return out


# =====================================================================
# 重建，非原版 — the 8 layouts below were NOT present in lesson-2-01.zh.html.
# Their CSS *is* original (theme.css already styles .agenda/.cmp/.metric/.it/
# .tl/.sched/.person/.quote/.podium); only the HTML structure inferred from
# those selectors and the animation timings are reconstructions.
# =====================================================================
def L_agenda(s, ctx):
    t0 = start(s)
    items = s['items']
    one = s.get('one_column', len(items) <= 3)
    c = f'<div class="agenda{" one" if one else ""}">'
    for k, it in enumerate(items):
        it = it if isinstance(it, dict) else {'t': it}
        c += (f'<div class="ag" data-a="rise"{d(t0 + 80 * k)}><div class="n">{inl(it.get("num", f"{k + 1:02d}"))}</div>'
              f'<div><div class="t">{inl(it["t"])}</div>{f"<div class=\"s\">{inl(it[chr(115)])}</div>" if it.get("s") else ""}</div>'
              f'{f"<div class=\"tm\">{inl(it[chr(116) + chr(109)])}</div>" if it.get("tm") else ""}</div>')
    c += '</div>'
    return body(s, c)


def L_compare(s, ctx):
    t0 = start(s)
    def side(x, k, good):
        h = f'<div class="side{" good" if good else ""}" data-a="rise"{d(t0 + 120 * k)}>'
        if x.get('badge'):
            h += f'<span class="badge">{inl(x["badge"])}</span>'
        h += f'<h3>{inl(x.get("title", ""))}</h3><ul>' + ''.join(f'<li>{inl(i)}</li>' for i in x.get('items', [])) + '</ul></div>'
        return h
    left, right = s['left'], s['right']
    c = '<div class="cmp">' + side(left, 0, left.get('good', False))
    c += f'<div class="vs" data-a="pop"{d(t0 + 60)}>{inl(s.get("vs", "VS"))}</div>'
    c += side(right, 1, right.get('good', True)) + '</div>'
    return body(s, c)


def _count_span(v, dec, sep, delay):
    shown = f'{float(v):,.{dec}f}' if sep else f'{float(v):.{dec}f}'
    return f'<span data-count="{v}" data-dec="{dec}" data-sep="{1 if sep else 0}" data-delay="{delay}">{shown}</span>'


def L_metrics(s, ctx):
    t0 = start(s)
    ms = s['items']
    n = len(ms)
    c = f'<div class="metrics{" m4" if n >= 4 else ""}" style="grid-template-columns:repeat({n},1fr)">'
    for k, m in enumerate(ms):
        dl = t0 + 100 * k
        v = m['value']
        val = _count_span(v, int(m.get('dec', 0)), bool(m.get('sep', False)), dl + 100) if isinstance(v, (int, float)) else inl(v)
        c += (f'<div class="metric" data-a="rise"{d(dl)}><div class="v">'
              f'{f"<span class=\"pf\">{inl(m[chr(112) + chr(102)])}</span>" if m.get("pf") else ""}{val}'
              f'{f"<span class=\"u\">{inl(m[chr(117)])}</span>" if m.get("u") else ""}</div>'
              f'<div class="rule" data-a="draw"{d(dl + 200)}></div><div class="l">{inl(m.get("l", ""))}</div>'
              f'{f"<div class=\"s\">{inl(m[chr(115)])}</div>" if m.get("s") else ""}</div>')
    c += '</div>'
    return body(s, c)


def data_uri(path, ctx):
    import mimetypes
    p = path if os.path.isabs(path) else os.path.join(ctx['base_dir'], path)
    if not os.path.exists(p):
        p2 = os.path.join(ASSETS, path)
        if not os.path.exists(p2):
            sys.exit(f'image not found: {path}')
        p = p2
    mt = mimetypes.guess_type(p)[0] or 'image/png'
    return f'data:{mt};base64,{b64(p)}'


PH_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
          'stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>'
          '<path d="M21 15l-5-5L5 21"/></svg>')


def L_image_text(s, ctx):
    t0 = start(s)
    img = s.get('image')
    med = f'<div class="it-media{" contain" if s.get("contain") else ""}" data-a="pop"{d(t0)}>'
    if img:
        med += f'<img src="{data_uri(img, ctx)}" alt="{attr(s.get("alt", ""))}">'
    else:
        med += f'<div class="ph">{PH_SVG}<span>{inl(s.get("placeholder", "图片占位"))}</span></div>'
    if s.get('caption'):
        med += f'<div class="it-cap">{inl(s["caption"])}</div>'
    med += '</div>'
    txt = '<div class="it-text">'
    if s.get('text'):
        txt += f'<p data-a="rise"{d(t0 + 120)}>{inl(s["text"])}</p>'
    if s.get('items'):
        txt += '<ul>' + ''.join(f'<li data-a="left"{d(t0 + 220 + 80 * k)}>{inl(i)}</li>' for k, i in enumerate(s['items'])) + '</ul>'
    txt += '</div>'
    return body(s, f'<div class="it{" right" if s.get("media_right") else ""}">{med}{txt}</div>')


def L_timeline(s, ctx):
    t0 = start(s)
    items = s['items']
    if s.get('variant', 'axis') == 'schedule':
        c = '<div class="sched">'
        for k, it in enumerate(items):
            c += (f'<div class="sc" data-a="left"{d(t0 + 80 * k)}><div class="tm">{inl(it.get("tm", ""))}</div>'
                  f'<div><div class="t">{inl(it.get("t", ""))}</div>{f"<div class=\"s\">{inl(it[chr(115)])}</div>" if it.get("s") else ""}</div></div>')
        return body(s, c + '</div>')
    c = f'<div class="tl" style="grid-template-columns:repeat({len(items)},1fr)"><div class="axis" data-a="draw"{d(t0)}></div>'
    for k, it in enumerate(items):
        c += (f'<div class="tli{" on" if it.get("on") else ""}" data-a="rise"{d(t0 + 110 * k)}><div class="tm">{inl(it.get("tm", ""))}</div>'
              f'<div class="pt"></div><div class="t">{inl(it.get("t", ""))}</div>'
              f'{f"<div class=\"s\">{inl(it[chr(115)])}</div>" if it.get("s") else ""}</div>')
    return body(s, c + '</div>')


def L_people(s, ctx):
    t0 = start(s)
    ps = s['items']
    c = f'<div class="people" style="grid-template-columns:repeat({s.get("cols", len(ps))},1fr)">'
    for k, p in enumerate(ps):
        col = p.get('color', [None, 'c2', 'c3'][k % 3])
        av = f'<img src="{data_uri(p["photo"], ctx)}" alt="">' if p.get('photo') else inl(p.get('initials', p['n'][:1]))
        c += (f'<div class="person" data-a="rise"{d(t0 + 90 * k)}><div class="avatar{(" " + col) if col else ""}">{av}</div>'
              f'<div class="n">{inl(p["n"])}</div>{f"<div class=\"r\">{inl(p[chr(114)])}</div>" if p.get("r") else ""}'
              f'{f"<div class=\"o\">{inl(p[chr(111)])}</div>" if p.get("o") else ""}</div>')
    return body(s, c + '</div>')


def L_quote(s, ctx):
    out = f'<div class="quote"><div class="qm" data-a="fade"{d(120)}>“</div>'
    out += f'<blockquote data-a="rise"{d(220)}>{inl(s["quote"])}</blockquote>'
    out += f'<div class="rule" data-a="draw"{d(420)}></div>'
    if s.get('who'):
        out += f'<div class="who" data-a="rise"{d(520)}>{inl(s["who"])}{f"<span>{inl(s[chr(114) + chr(111) + chr(108) + chr(101)])}</span>" if s.get("role") else ""}</div>'
    return out + '</div>'


def L_podium(s, ctx):
    t0 = start(s)
    top = s['items'][:3]                      # given in rank order 1,2,3; shown 2-1-3
    order = [1, 0, 2][:len(top)] if len(top) == 3 else list(range(len(top)))
    c = '<div class="podium">'
    for j, idx in enumerate(order):
        it, rank = top[idx], idx + 1
        dl = t0 + [200, 0, 400][rank - 1]
        c += (f'<div class="pd r{rank}" data-a="rise"{d(dl + 300)}><div class="medal">{rank}</div>'
              f'<div class="t">{inl(it.get("t", ""))}</div>{f"<div class=\"w\">{inl(it[chr(119)])}</div>" if it.get("w") else ""}'
              f'{f"<div class=\"p\">{inl(it[chr(112)])}</div>" if it.get("p") else ""}'
              f'<div class="block" data-a="grow"{d(dl)}>{rank}</div></div>')
    c += '</div>'
    if s.get('awards'):
        c += f'<div class="awards" data-a="fade"{d(t0 + 900)}>' + ''.join(f'<span class="pill">{inl(a)}</span>' for a in s['awards']) + '</div>'
    return body(s, c)



# =====================================================================
# NEW layout "diagram" (not in the original 2-01 file): SVG scene + timeline.
# The DOM is emitted in its final state; assets/templates/diagram.js resets & plays on entry.
# =====================================================================
def _lines(t):
    return str(t).split('\n')


def _svg_text(x, y, text, size, cls='', anchor='middle', weight=None, lh=1.3):
    ls = _lines(text)
    w = f' font-weight="{weight}"' if weight else ''
    c = f' class="{cls}"' if cls else ''
    if len(ls) == 1:
        return f'<text{c} x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}"{w}>{esc(ls[0])}</text>'
    out = f'<text{c} x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}"{w}>'
    for k, l in enumerate(ls):
        out += f'<tspan x="{x}" dy="{0 if k == 0 else round(size * lh)}">{esc(l)}</tspan>'
    return out + '</text>'


def _icon_inner(name):
    full = icon(name)
    return full[full.index('>') + 1:full.rindex('</svg>')]


def _el(e, st):
    """Render one scene element in its FINAL state.  st = dict(fin_k, fin_on, fin_hidden, fin_text, fin_tk)."""
    t, i = e['type'], e['id']
    pre = ' pre' if i in st['hidden'] else ''
    on = ' on' if i in st['on'] else ''
    if t == 'box':
        x, y, w, h = e['x'], e['y'], e['w'], e['h']
        k = st['k'].get(i, e.get('kind', 'neutral'))
        label = st['text'].get(i, e.get('label', ''))
        ls, ss = e.get('size', 28), e.get('sub_size', 22)
        out = f'<g class="de bx{" sh" if e.get("shadow", True) else ""}{on}{pre}" data-id="{i}" data-k="{k}">'
        out += f'<rect class="s" x="{x}" y="{y}" width="{w}" height="{h}" rx="{e.get("r", 18)}"/>'
        if e.get('align') == 'tl':      # container: label top-left
            if e.get('icon'):
                out += f'<svg class="ic" x="{x + 22}" y="{y + 18}" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{_icon_inner(e["icon"])}</svg>'
            lx = x + (66 if e.get('icon') else 24)
            out += _svg_text(lx, y + 46, label, ls, 'lb', 'start', 700)
            if e.get('sub'):
                out += _svg_text(lx + e.get('sub_dx', 0), y + 46 + e.get('sub_dy', 34), e['sub'], ss, 'sub', 'start')
            return out + '</g>'
        nl, ns = len(_lines(label)), len(_lines(e['sub'])) if e.get('sub') else 0
        ih = 46 if e.get('icon') else 0
        total = ih + nl * ls * 1.25 + (ns * ss * 1.3 + 8 if ns else 0)
        cy = y + (h - total) / 2
        cx = x + w / 2
        if e.get('icon'):
            out += f'<svg class="ic" x="{cx - 19:.0f}" y="{cy:.0f}" width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{_icon_inner(e["icon"])}</svg>'
            cy += ih
        out += _svg_text(round(cx), round(cy + ls * 0.95), label, ls, 'lb' + (' mono' if e.get('mono') else ''), 'middle', 700, 1.25)
        if ns:
            out += _svg_text(round(cx), round(cy + nl * ls * 1.25 + 8 + ss * 0.95), e['sub'], ss, 'sub', 'middle', None)
        return out + '</g>'
    if t == 'text':
        cls = ' '.join(c for c in [e.get('font', ''), f'c-{e["color"]}' if e.get('color') else ''] if c)
        return (f'<g class="de tx{pre}" data-id="{i}">' + _svg_text(e['x'], e['y'], st['text'].get(i, e['text']), e.get('size', 24), cls,
                e.get('anchor', 'middle'), e.get('weight', 500)) + '</g>')
    if t == 'arrow':
        pts = e['points']
        dd = 'M' + ' L'.join(f'{p[0]} {p[1]}' for p in pts)
        col = {'orange': ' o', 'blue': ' b'}.get(e.get('color'), '')
        mode = e.get('mode', 'draw')
        mk = {'orange': 'o', 'blue': 'b'}.get(e.get('color'), 'g')
        head = f' marker-end="url(#dgm{st["n"]}-mk-{mk})"' if e.get('head', True) else ''
        pl = ' pathLength="1"' if mode == 'draw' else ''
        out = f'<g class="de ar{col} {mode}{pre}" data-id="{i}"><path d="{dd}"{pl}{head}/>'
        if e.get('label'):
            lx, ly = e.get('label_at', [(pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2 - 16])
            out += _svg_text(round(lx), round(ly), e['label'], e.get('size', 20), 'sub c-ink3', 'middle', 500)
        return out + '</g>'
    if t == 'token':
        w, h = e.get('w', 120), e.get('h', 44)
        fx, fy = st['tk'].get(i, [e['x'], e['y']])
        k = st['k'].get(i, e.get('kind', 'dark'))
        return (f'<g class="de tk{pre}" data-id="{i}" data-k="{k}"><g class="mv" transform="translate({fx},{fy})">'
                f'<rect x="{-w / 2:g}" y="{-h / 2:g}" width="{w}" height="{h}" rx="{h / 2:g}"/>'
                + _svg_text(0, round(e.get('size', 22) * 0.36), st['text'].get(i, e.get('label', '')), e.get('size', 22),
                            'mono' if e.get('mono') else '', 'middle', 700) + '</g></g>')
    if t == 'band':
        out = f'<g class="de bd{" b" if e.get("color") == "blue" else ""}{pre}" data-id="{i}"><rect x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" rx="{e.get("r", 22)}"/>'
        if e.get('label'):
            lx, ly = e.get('label_at', [e['x'] + 18, e['y'] - 14])
            out += _svg_text(lx, ly, e['label'], e.get('size', 22), '', e.get('anchor', 'start'), 700)
        return out + '</g>'
    if t == 'grid':
        out = f'<g class="de gr{on}{pre}" data-id="{i}">'
        c, g = e.get('cell', 22), e.get('gap', 6)
        for r_ in range(e['rows']):
            for c_ in range(e['cols']):
                out += (f'<rect class="cell" x="{e["x"] + c_ * (c + g)}" y="{e["y"] + r_ * (c + g)}" width="{c}" height="{c}" '
                        f'rx="{max(2, c // 5)}" style="--i:{r_ + c_}"/>')
        return out + '</g>'
    if t == 'bytes':
        k = st['k'].get(i, e.get('kind', 'f32'))
        s_, g = e.get('cell', 44), e.get('gap', 10)
        out = f'<g class="de by{pre}" data-id="{i}" data-k="{k}">'
        for j in range(e['n']):
            out += f'<rect x="{e["x"] + j * (s_ + g)}" y="{e["y"]}" width="{s_}" height="{s_}"/>'
        if e.get('label'):
            out += _svg_text(e['x'] + (e['n'] * (s_ + g) - g) / 2, e['y'] + s_ + 34, e['label'], e.get('size', 22), 'mono c-ink3', 'middle', 600)
        return out + '</g>'
    if t == 'images':
        out = f'<g class="de im{pre}" data-id="{i}">'
        w, h, g, cols = e.get('w', 76), e.get('h', 56), e.get('gap', 12), e.get('cols', 5)
        for j in range(e['n']):
            x = e['x'] + (j % cols) * (w + g); y = e['y'] + (j // cols) * (h + g)
            out += (f'<g class="t" style="--i:{j}"><rect class="f" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
                    f'<path d="M{x + 8} {y + h - 8} L{x + w * .38:.0f} {y + h * .45:.0f} L{x + w * .6:.0f} {y + h * .7:.0f} L{x + w * .75:.0f} {y + h * .55:.0f} L{x + w - 8} {y + h - 8} Z"/>'
                    f'<circle cx="{x + w * .74:.0f}" cy="{y + h * .3:.0f}" r="{h * .1:.0f}"/></g>')
        return out + '</g>'
    if t == 'photo':        # product photo (data URI) or a clean dashed outline placeholder
        x, y, w, h = e['x'], e['y'], e['w'], e['h']
        out = f'<g class="de ph{on}{pre}" data-id="{i}">'
        if e.get('src'):
            out += (f'<image href="{data_uri(e["src"], st["ctx"])}" x="{x}" y="{y}" width="{w}" height="{h}" '
                    f'preserveAspectRatio="{e.get("fit", "xMidYMax meet")}"/>')
        else:
            out += f'<rect class="phx" x="{x}" y="{y}" width="{w}" height="{h}" rx="18"/>'
            if e.get('label'):
                out += _svg_text(x + w / 2, y + h / 2 + 8, e['label'], e.get('size', 22), 'sub', 'middle', 500)
        return out + '</g>'
    if t == 'meter':        # horizontal bar; fills to value (0..1) when the element is "on"
        x, y, w, h = e['x'], e['y'], e['w'], e['h']
        k = st['k'].get(i, e.get('kind', 'bpu'))
        v = max(0.0, min(1.0, float(e['value'])))
        out = f'<g class="de mt{on}{pre}" data-id="{i}" data-k="{k}"><rect class="trk" x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2:g}"/>'
        out += f'<rect class="fill" x="{x}" y="{y}" width="{max(h, w * v):.1f}" height="{h}" rx="{h / 2:g}"/>'
        if e.get('label'):
            out += _svg_text(x - 18, y + h / 2 + e.get('size', 24) * .36, e['label'], e.get('size', 24), e.get('label_cls', ''), 'end', 700)
        if e.get('vlabel'):
            out += _svg_text(x + max(h, w * v) + 14, y + h / 2 + e.get('size', 24) * .36, e['vlabel'], e.get('size', 24), 'v mono', 'start', 700)
        return out + '</g>'
    if t == 'hist':         # vertical histogram (illustrative shape), bars grow from the baseline
        x, y, w, h, vals = e['x'], e['y'], e['w'], e['h'], e['values']
        g = e.get('gap', 4); bw = (w - g * (len(vals) - 1)) / len(vals); mx = max(vals) or 1
        out = f'<g class="de hs{on}{pre}" data-id="{i}">'
        for j, v in enumerate(vals):
            bh = h * v / mx
            out += f'<rect x="{x + j * (bw + g):.1f}" y="{y + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{min(4, bw / 3):.1f}" style="--i:{j}"/>'
        out += f'<path class="base" d="M{x - 10} {y + h} L{x + w + 10} {y + h}"/>'
        return out + '</g>'
    if t == 'levels':       # n evenly spaced thin ticks (e.g. the 256 int8 levels)
        x, y, w, h, n = e['x'], e['y'], e['w'], e['h'], e['n']
        dd = ''.join(f'M{x + w * j / (n - 1):.2f} {y} L{x + w * j / (n - 1):.2f} {y + h} ' for j in range(n))
        return f'<g class="de lv{on}{pre}" data-id="{i}"><path d="{dd.strip()}"/></g>'
    sys.exit(f'diagram: unknown element type {t}')


def L_diagram(s, ctx):
    ctx['diagram'] = True
    scene, steps = s['scene'], s.get('steps', [])
    W, H = 1600, s.get('height', 560)
    ids = {e['id'] for e in scene}
    for stp in steps:
        for key in ('show', 'hide', 'on', 'off', 'focus'):
            for x in (stp.get(key) or []):
                if x not in ids:
                    sys.exit(f'slide "{s.get("title")}": step references unknown id "{x}"')
    shown_ever = {x for stp in steps for x in stp.get('show', [])}
    init_pre = [e['id'] for e in scene if e['id'] in shown_ever and not e.get('visible')]
    vis = {e['id']: e['id'] not in init_pre for e in scene}
    on = {e['id'] for e in scene if e.get('on')}
    init_on = sorted(on)
    kinds_init, kinds = {}, {}
    texts_init, texts = {}, {}
    byid = {e['id']: e for e in scene}
    for stp in steps:
        for x in stp.get('show', []): vis[x] = True
        for x in stp.get('hide', []): vis[x] = False
        on |= set(stp.get('on', [])); on -= set(stp.get('off', []))
        for x, v in (stp.get('state') or {}).items():
            kinds_init.setdefault(x, byid[x].get('kind', 'neutral'))
            kinds[x] = v
        for x, v in (stp.get('text') or {}).items():
            texts_init.setdefault(x, byid[x].get('label', byid[x].get('text', '')))
            texts[x] = v
    tk_init, tk_fin = {}, {}
    hidden = {x for x, v in vis.items() if not v}
    for e in scene:
        if e['type'] != 'token':
            continue
        tk_init[e['id']] = [e['x'], e['y']]
        last = None
        for stp in steps:
            for m in stp.get('move', []):
                if m['id'] == e['id']:
                    last = m['path'][-1][:2]
        rest = e.get('rest', 'end')
        if rest == 'hide':
            hidden.add(e['id'])
        elif rest == 'end':
            tk_fin[e['id']] = last or [e['x'], e['y']]
        else:
            tk_fin[e['id']] = rest
    ctx['dgm_n'] = ctx.get('dgm_n', 0) + 1
    st = {'hidden': hidden, 'on': on, 'k': kinds, 'text': texts, 'tk': tk_fin, 'n': ctx['dgm_n'], 'ctx': ctx}
    caps = []
    tl_steps = []
    for stp in steps:
        o = {k: v for k, v in stp.items() if k != 'note'}
        if 'caption' in stp:
            o['capIndex'] = len(caps); caps.append(stp['caption'])
        tl_steps.append(o)
    end = max([stp.get('at', 0) for stp in steps] + [0]) + 2500
    final_cap = s.get('final_caption', caps[-1] if caps else '')
    tl = {'W': W, 'H': H, 'delay': s.get('delay', 450), 'end': end, 'steps': tl_steps,
          'init': {'pre': init_pre, 'on': init_on, 'k': kinds_init, 'text': texts_init, 'tk': tk_init, 'cap': ''},
          'fin': {'k': kinds, 'on': sorted(on), 'hidden': sorted(hidden), 'text': texts, 'tk': tk_fin}}
    defs = ('<defs>' + ''.join(f'<marker id="dgm{st["n"]}-mk-{n}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
                               f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>' for n, c in (('g', '#BDC1C6'), ('o', '#FF5A00'), ('b', '#1A73E8')))
            + '</defs>')
    body_svg = ''.join(_el(e, st) for e in scene)
    svg = (f'<svg class="dg-svg" viewBox="0 0 {W} {H}" style="height:{H}px" xmlns="http://www.w3.org/2000/svg">{defs}'
           f'<g class="cam">{body_svg}</g></svg>')
    capbar = ''
    if caps:
        capbar = (f'<div class="dgm-cap"><i></i><span class="t">{inl(final_cap)}</span>'
                  f'<span class="st">{"".join("<b class=\"on\"></b>" for _ in caps)}</span></div>')
    data = json.dumps(tl, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    t0 = start(s)
    c = (f'<div class="dgm" data-a="fade"{d(t0 - 120)}>{svg}{capbar}'
         f'<script type="application/json" class="dgm-tl">{data}</script></div>')
    return body(s, c)



LAYOUTS = {'cover': L_cover, 'section': L_section, 'cards': L_cards, 'flow': L_flow, 'table': L_table,
           'bullets': L_bullets, 'code': L_code, 'bars': L_bars, 'links': L_links, 'closing': L_closing,
           # 重建，非原版
           'agenda': L_agenda, 'compare': L_compare, 'metrics': L_metrics, 'image-text': L_image_text,
           'timeline': L_timeline, 'people': L_people, 'quote': L_quote, 'podium': L_podium,
           # NEW (2026-10): animated SVG diagram
           'diagram': L_diagram}
RECOVERED = ['cover', 'cards', 'section', 'bullets', 'code', 'flow', 'table', 'bars', 'links', 'closing']
REBUILT = ['agenda', 'compare', 'metrics', 'image-text', 'timeline', 'people', 'quote', 'podium']
NO_FOOT = {'cover', 'section', 'closing', 'quote'}
DEFAULT_BG = {'cover': 'white'}


def render_slide(s, i, n, meta, ctx):
    lay = s['layout']
    if lay not in LAYOUTS:
        sys.exit(f'slide {i + 1}: layout "{lay}" is not one of the recovered layouts: {", ".join(LAYOUTS)}')
    cls = 'slide' + (' dark' if s.get('dark') else '')
    title = s.get('title', '')
    bg = BG[s.get('bg', 'dark' if s.get('dark') else DEFAULT_BG.get(lay, 'stage'))]
    out = f'<section class="{cls}" data-layout="{lay}" data-title="{attr(title)}">{bg}'
    out += LAYOUTS[lay](s, ctx)
    out += '<i class="logo" aria-label="D-Robotics"></i>'
    if meta.get('tag'):
        out += f'<div class="tag-tr"><i></i>{inl(meta["tag"])}</div>'
    if s.get('foot', lay not in NO_FOOT):
        out += (f'<div class="foot"><span>{inl(meta.get("footer", ""))} · <b>{inl(title)}</b></span>'
                f'<span>{i + 1:02d} / {n:02d}</span></div>')
    if s.get('notes'):
        out += f'<aside class="notes">{inl(s["notes"])}</aside>'
    return out + '</section>\n'


# ---------------------------------------------------------------- fonts
# placeholder, bundled subset, env var, TTC face name, filenames, extra system paths.
# Full source fonts are not bundled. See references/fonts.md.
FONT_SLOTS = [
    ('FONT_CJK_400', 'dg-cjk-400.woff2', 'DG_FONT_CJK_REGULAR', 'Noto Sans CJK SC',
     ['NotoSansCJK-Regular.ttc', 'NotoSansCJKsc-Regular.otf'],
     ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
      '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
      '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc']),
    ('FONT_CJK_700', 'dg-cjk-700.woff2', 'DG_FONT_CJK_BOLD', 'Noto Sans CJK SC',
     ['NotoSansCJK-Bold.ttc', 'NotoSansCJKsc-Bold.otf'],
     ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
      '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf',
      '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc']),
    ('FONT_SANS', 'dg-sans-outfit-var.woff2', 'DG_FONT_SANS', None,
     ['Outfit-VariableFont_wght.ttf', 'Outfit[wght].ttf'],
     ['/usr/share/fonts/truetype/outfit/Outfit-VariableFont_wght.ttf',
      '/usr/share/fonts/truetype/outfit/Outfit[wght].ttf']),
    ('FONT_MONO', 'dg-mono-jetbrains-var.woff2', 'DG_FONT_MONO', None,
     ['JetBrainsMono-VariableFont_wght.ttf', 'JetBrainsMono[wght].ttf', 'JetBrainsMono-Regular.ttf'],
     ['/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono[wght].ttf',
      '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-VariableFont_wght.ttf',
      '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf']),
]
# always kept on top of the deck's own rendered text (observed in the original subsets: ? — … ≤ ✓)
EXTRA_CHARS = ' ?—…≤✓'


def used_chars(fragment):
    t = re.sub(r'<script>.*?</script>|<style>.*?</style>', '', fragment, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    return set(html.unescape(t)) - set('\n\r\t')


def find_font_source(env, names, system):
    """First existing source font: $ENV, assets/fonts/sources/, user font dirs, then system paths."""
    candidates = []
    env_path = os.environ.get(env)
    if env_path:
        candidates.append(env_path)
    bases = [os.path.join(ASSETS, 'fonts', 'sources'),
             os.path.expanduser('~/.local/share/fonts'),
             os.path.expanduser('~/Library/Fonts')]
    for base in bases:
        for name in names:
            candidates.append(os.path.join(base, name))
    candidates.extend(system)
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def load_source(path, name):
    from fontTools.ttLib import TTFont, TTCollection
    if path.lower().endswith('.ttc'):
        for f in TTCollection(path).fonts:
            face = f['name'].getDebugName(1)
            typo = f['name'].getDebugName(16)
            if name is None or face == name or typo == name:
                return f
        raise SystemExit(f'{name} not found in {path}')
    return TTFont(path)


def subset_font(src, chars):
    from fontTools import subset
    opts = subset.Options()
    opts.layout_features = ['*']
    opts.flavor = 'woff2'
    opts.name_IDs = ['*']
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=[ord(c) for c in chars])
    sub.subset(src)
    buf = io.BytesIO()
    src.flavor = 'woff2'
    src.save(buf)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def fonts(chars, force_resubset, log):
    from fontTools.ttLib import TTFont
    res = {}
    for ph, bundled, env, ttcname, names, system in FONT_SLOTS:
        bpath = os.path.join(ASSETS, 'fonts', bundled)
        srcpath = find_font_source(env, names, system)
        need_sub = force_resubset
        missing = set()
        if not need_sub:
            have = set(TTFont(bpath).getBestCmap())
            missing = {ord(c) for c in chars} - have
            if missing:
                if not srcpath:
                    log(f'  ! {bundled}: {len(missing)} chars not in bundled subset and no source font found '
                        f'(set {env} or see references/fonts.md) -> those chars fall back to system fonts')
                else:
                    srccmap = set(load_source(srcpath, ttcname).getBestCmap())
                    need_sub = bool(missing & srccmap)
                    if need_sub:
                        log(f'  {bundled}: missing {"".join(sorted(chr(c) for c in missing & srccmap))[:60]}')
                    else:
                        missing = set()
        if need_sub:
            if not srcpath:
                raise SystemExit(f'{bundled}: --resubset needs a source font. Set {env} or see references/fonts.md')
            src = load_source(srcpath, ttcname)
            keep = ''.join(sorted(c for c in chars if ord(c) in set(src.getBestCmap())))
            res[ph] = subset_font(src, keep)
            log(f'  {bundled}: re-subset from {srcpath} ({len(keep)} chars)')
        else:
            res[ph] = b64(bpath)
            if missing:
                log(f'  {bundled}: bundled subset embedded; characters it does not cover fall back to system fonts')
            else:
                log(f'  {bundled}: bundled subset covers all chars, embedded verbatim')
    return res


# ---------------------------------------------------------------- main
def build(spec, force_resubset=False, log=print, base_dir='.'):
    meta, slides = spec['meta'], spec['slides']
    n = len(slides)
    secs = [s for s in slides if s['layout'] == 'section']
    ctx = {'base_dir': base_dir, 'toc': [f'{s["num"]} · {s.get("toc_title", s.get("heading", ""))}' for s in secs],
           'logo_full': b64(os.path.join(ASSETS, 'brand', meta.get('logo_full', 'd-robotics-logo-full.png')))}
    out, si = '', -1
    for i, s in enumerate(slides):
        if s['layout'] == 'section':
            si += 1
        ctx['section_index'] = si
        out += render_slide(s, i, n, meta, ctx)

    page = rd(os.path.join(TPL, 'page.html'))
    ui_part = page[page.index('{{SLIDES}}') + len('{{SLIDES}}'):]
    chars = used_chars(out) | used_chars(ui_part.split('<script>')[0]) | set(meta['title']) | set(EXTRA_CHARS)
    f = fonts(chars, force_resubset, log)
    css = rd(os.path.join(TPL, 'fonts.css.tmpl'))
    for k, v in f.items():
        css = css.replace('{{' + k + '}}', v)
    css += rd(os.path.join(TPL, 'theme.css'))
    if ctx.get('ext'):
        css = css.rstrip('\n') + '\n' + rd(os.path.join(TPL, 'ext.css')).lstrip('\n') + '\n'
    if ctx.get('diagram'):
        css = css.rstrip('\n') + '\n' + rd(os.path.join(TPL, 'diagram.css')).lstrip('\n') + '\n'
    theme = ''.join(f'--dg-{k}:{v};' for k, v in (meta.get('theme') or {}).items())
    css += (rd(os.path.join(TPL, 'brand.css.tmpl'))
            .replace('{{THEME_VARS}}', theme)
            .replace('{{LOGO_PNG}}', b64(os.path.join(ASSETS, 'brand', meta.get('logo', 'd-robotics-icon.png'))))
            .replace('{{LOGO_DARK_PNG}}', b64(os.path.join(ASSETS, 'brand', meta.get('logo_dark', 'd-robotics-icon-dark.png')))))
    rep = {'{{LANG}}': attr(meta.get('lang', 'zh-CN')), '{{MODE}}': attr(meta.get('mode', 'deck')),
           '{{BOOT_JS}}': rd(os.path.join(TPL, 'boot.js')), '{{RUNTIME_JS}}': rd(os.path.join(TPL, 'runtime.js')) + (rd(os.path.join(TPL, 'diagram.js')) + '\n' if ctx.get('diagram') else '')}
    for k, v in rep.items():
        page = page.replace(k, v)
    page = page.replace('{{TITLE}}', attr(meta['title']))
    page = page.replace('{{CSS}}', css).replace('{{SLIDES}}', out)   # last: no placeholders inside user content get expanded
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec')
    ap.add_argument('-o', '--out')
    ap.add_argument('--resubset', action='store_true', help='always re-subset fonts from the system source fonts')
    a = ap.parse_args()
    spec = json.loads(rd(a.spec))
    out = a.out or os.path.splitext(a.spec)[0] + '.html'
    print(f'building {a.spec} ({len(spec["slides"])} slides)')
    page = build(spec, a.resubset, base_dir=os.path.dirname(os.path.abspath(a.spec)))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'-> {out} ({len(page.encode()) / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
