"""Series cover ("RDK 小课堂" / "RDK Classroom") shared by build.py and render_cover.py.

One template, one set of fields:
  * build.py renders it as the `series-cover` slide layout (slide 1 of every lesson deck);
  * render_cover.py builds a one-slide deck from the same fields and screenshots its final
    frame, so the platform thumbnail and slide 1 are pixel-for-pixel the same design.

Fields (slide object):
  chapter (int), chapter_name, lesson (int), title, highlight, subtitle, visual, lang
  optional: series, badge, theme (light | dark | orange; light is the approved series style),
            nav_title, mock (true = "MOCK-UP" stamp for template previews only)

Text fields are plain text (HTML-escaped). In `title`, "\\n" (or a real newline) breaks the line, and
the substring `highlight` (or a ==word== span) is drawn in brand orange.
"""
import html as _html, json
import re

ORANGE, ORANGE_DEEP, BLUE = '#FF5A00', '#FF3C00', '#1A73E8'
TEXT_W, VIS_SIZE, VIS_X = 760, 600, 1070      # text column 280..1040, visual 1070..1670 (inside the 4:3 safe area)
SAFE_X0, SAFE_X1 = 240, 1680                  # centre 4:3 crop of a 1920x1080 frame

THEMES = {
    'light':  dict(bg='#F4F5F7', ink='#202124', ink2='#3C4043', ink3='#5F6368', line='#DADCE0',
                   chip='#FFFFFF', chip_edge='#E3E5E8', die='#FFF3EA', pin='#C4C8CE', cell_lo='#FFD9C2', plate='#FFFFFF',
                   plate_ink=ORANGE_DEEP, title_accent=ORANGE_DEEP, stroke=ORANGE, glow='rgba(255,90,0,.20)',
                   tag_bg=ORANGE, tag_ink='#FFFFFF', shadow='.16',
                   wordmark='d-robotics-logo-full.png', wordmark_en='d-robotics-logo-full-en.png'),
    'dark':   dict(bg='#111214', ink='#F8F9FA', ink2='#E8EAED', ink3='#BDC1C6', line='rgba(255,255,255,.16)',
                   chip='#202227', chip_edge='#33363D', die='#16171A', pin='#4A4E57', cell_lo='#4A2A1A', plate='#111214',
                   plate_ink='#FF7828', title_accent='#FF7828', stroke=ORANGE, glow='rgba(255,90,0,.42)',
                   tag_bg=ORANGE, tag_ink='#FFFFFF', shadow='.35',
                   wordmark='d-robotics-logo-full-dark.png', wordmark_en='d-robotics-logo-full-en-dark.png'),
    'orange': dict(bg=ORANGE_DEEP, ink='#FFFFFF', ink2='#FFFFFF', ink3='rgba(255,255,255,.88)', line='rgba(255,255,255,.35)',
                   chip='#FFFFFF', chip_edge='rgba(0,0,0,0)', die='#FFF3EA', pin='rgba(255,255,255,.75)', cell_lo='#FFD9C2', plate='#FFFFFF',
                   plate_ink=ORANGE_DEEP, title_accent='#FFFFFF', stroke='#FFFFFF', glow='rgba(255,255,255,.18)',
                   tag_bg='#202124', tag_ink='#FFFFFF', shadow='.16',
                   wordmark='d-robotics-logo-full-white.png', wordmark_en='d-robotics-logo-full-en-white.png'),
}

STR = {
    'zh': dict(series='RDK 小课堂', nav='封面', mock='MOCK-UP · 示意，非正式封面',
               chapter='第 {} 章', lesson='第 {} 课', sep='｜'),
    'en': dict(series='RDK Classroom', nav='Cover', mock='MOCK-UP · not the final cover',
               chapter='Chapter {}', lesson='Lesson {}', sep='|'),
}
SANS = '"DG Sans","Outfit","DG CJK","Noto Sans CJK SC",sans-serif'
CJK = '"DG CJK","Noto Sans CJK SC","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif'


def lang_of(s, meta=None):
    lang = str(s.get('lang') or (meta or {}).get('lang') or 'zh')
    return 'en' if lang.lower().startswith('en') else 'zh'


def badge(s):
    return str(s['badge']) if s.get('badge') else f'{int(s["chapter"])}-{int(s["lesson"]):02d}'


def nav_title(s, meta=None):
    return s.get('nav') or s.get('nav_title') or STR[lang_of(s, meta)]['nav']


def series_title(s, meta=None):
    """Video / document title from the same fields.
    zh: 【RDK 小课堂】第 N 章 <章名> · 第 M 课｜<课名>   (N, M not zero-padded)
    en: [RDK Classroom] Chapter N <name> · Lesson M | <title>"""
    lang = lang_of(s, meta)
    t = re.sub(r'\s*(\\n|\n)\s*', ' ', re.sub(r'==(.+?)==', r'\1', s.get('title', ''))).strip()
    ser = s.get('series') or STR[lang]['series']
    if lang == 'en':
        return f'[{ser}] Chapter {int(s["chapter"])} {s["chapter_name"]} · Lesson {int(s["lesson"])} | {t}'
    return f'【{ser}】第 {int(s["chapter"])} 章 {s["chapter_name"]} · 第 {int(s["lesson"])} 课｜{t}'


FIELDS = ('chapter', 'chapter_name', 'lesson', 'title', 'highlight', 'accent', 'subtitle', 'visual', 'theme',
          'badge', 'series', 'mock', 'nav', 'nav_title')


def check(s, where='series-cover'):
    miss = [k for k in ('chapter', 'chapter_name', 'lesson', 'title') if s.get(k) in (None, '')]
    if miss:
        raise SystemExit(f'{where}: missing field(s) {", ".join(miss)}')
    if s.get('theme', 'light') not in THEMES:
        raise SystemExit(f'{where}: theme must be one of {", ".join(THEMES)}')


# ---------------------------------------------------------------- key visuals (600x600 viewBox)
def svg_bpu(t, uid='sc'):
    """BPU chip: package + pins + die with a MAC grid; blue input traces as the only blue accent."""
    o = []
    for i in range(9):
        c = 132 + i * 42
        o += [f'<rect x="{c-8}" y="22" width="16" height="44" rx="5" fill="{t["pin"]}"/>',
              f'<rect x="{c-8}" y="534" width="16" height="44" rx="5" fill="{t["pin"]}"/>',
              f'<rect x="534" y="{c-8}" width="44" height="16" rx="5" fill="{t["pin"]}"/>']
    for i in range(9):
        c = 132 + i * 42
        o.append(f'<rect x="22" y="{c-8}" width="44" height="16" rx="5" fill="{BLUE if i in (3, 4, 5) else t["pin"]}"/>')
    o.append(f'<rect x="60" y="60" width="480" height="480" rx="56" fill="{t["chip"]}" stroke="{t["chip_edge"]}" stroke-width="3"/>')
    o.append(f'<rect x="112" y="112" width="376" height="376" rx="30" fill="{t["die"]}" stroke="{ORANGE}" stroke-width="4"/>')
    n, cell, gap = 10, 27, 7
    x0 = 112 + (376 - (n * cell + (n - 1) * gap)) / 2
    for r in range(n):
        for c in range(n):
            v = (r + c) % 7
            fill = ORANGE if v in (0, 1, 2, 3) else ('#FF8A3D' if v in (4, 5) else t['cell_lo'])
            o.append(f'<rect x="{x0 + c*(cell+gap):.1f}" y="{x0 + r*(cell+gap):.1f}" width="{cell}" height="{cell}" rx="6" fill="{fill}"/>')
    o.append(f'<rect x="196" y="250" width="208" height="100" rx="22" fill="{t["plate"]}" filter="url(#{uid}-ps)"/>')
    o.append(f'<text x="300" y="322" text-anchor="middle" font-family="DG Sans, Outfit, sans-serif" font-weight="800" '
             f'font-size="70" fill="{t["plate_ink"]}" letter-spacing="2">BPU</text>')
    return (f'<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg"><defs><filter id="{uid}-ps" x="-20%" y="-30%" '
            'width="140%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000" flood-opacity=".22"/>'
            '</filter></defs>' + ''.join(o) + '</svg>')


def svg_quant(t, uid='sc'):
    """FP32 (blue, 4 bytes/value) -> INT8 (orange, 1 byte/value)."""
    o = []

    def card(x, y, w, h):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="36" fill="{t["chip"]}" stroke="{t["chip_edge"]}" stroke-width="3"/>')
    card(10, 90, 300, 420); card(370, 150, 220, 300)
    for r in range(4):
        for c in range(4):
            for b in range(4):
                o.append(f'<rect x="{46 + c*60 + (b%2)*24}" y="{170 + r*72 + (b//2)*24}" width="20" height="20" rx="4" '
                         f'fill="{BLUE}" opacity="{1 if b == 0 else .55}"/>')
    for r in range(4):
        for c in range(4):
            o.append(f'<rect x="{410 + c*38}" y="{210 + r*38}" width="28" height="28" rx="6" fill="{ORANGE}"/>')
    f = 'font-family="DG Sans, Outfit, sans-serif" font-weight="800" font-size="44"'
    o.append(f'<text x="160" y="150" text-anchor="middle" {f} fill="{BLUE}">FP32</text>')
    o.append(f'<text x="480" y="410" text-anchor="middle" {f} fill="{ORANGE}">INT8</text>')
    o.append(f'<path d="M318 300 h44" stroke="{t["ink3"]}" stroke-width="8" stroke-linecap="round"/><path d="M350 284 l18 16 l-18 16" '
             f'fill="none" stroke="{t["ink3"]}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')
    return '<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">' + ''.join(o) + '</svg>'


BUILTIN = {'bpu': svg_bpu, 'quant': svg_quant}


# ---------------------------------------------------------------- HTML
def _title_html(s):
    raw = str(s.get('title', '')).replace('\\n', '\n')
    hl = s.get('highlight') or s.get('accent')
    parts = re.split(r'(==.+?==)', raw)
    out, done = '', False
    for p in parts:
        if p.startswith('==') and p.endswith('==') and len(p) > 4:
            out += f'<em>{_html.escape(p[2:-2])}</em>'; done = True; continue
        e = _html.escape(p)
        if hl and not done and _html.escape(hl) in e:
            e = e.replace(_html.escape(hl), f'<em>{_html.escape(hl)}</em>', 1); done = True
        out += e
    return re.sub(r'\s*\n\s*', '<br>', out.strip())


def fragment(s, meta, img_src, logo_src, uid='sc1', animate=True):
    """Inner HTML of the slide. img_src(path) -> URL for an image visual; logo_src(file) -> URL of assets/brand/<file>.
    Elements carry dg-deck data-a/--d entrance attributes (total ~1.1 s); the un-animated DOM is the final frame."""
    check(s)
    lang = lang_of(s, meta)
    L = STR[lang]
    theme = s.get('theme', 'light')
    t = THEMES[theme]
    esc = _html.escape

    def a(kind, ms):
        return f' data-a="{kind}" style="--d:{ms};"' if animate else ''
    ser = s.get('series') or L['series']
    lab = (f'<i class="sc-ls"></i><span>{L["chapter"].format(int(s["chapter"]))}</span><span class="sc-dot">·</span>'
           f'<span>{esc(str(s["chapter_name"]))}</span><span class="sc-dot">{L["sep"]}</span>'
           f'<span class="sc-ln">{L["lesson"].format(int(s["lesson"]))}</span>')
    vis = s.get('visual', 'bpu')
    if vis in BUILTIN:
        vis_html = BUILTIN[vis](t, uid)
    elif vis:
        vis_html = f'<img src="{img_src(vis)}" alt="">'
    else:
        vis_html = ''
    o = f'<div class="sc sc-{theme} sc-{lang}">'
    o += f'<div class="bg sc-bg"><i class="sc-panel"></i><i class="sc-glow"{a("fade", 200)}></i></div>'
    o += (f'<div class="sc-lock"{a("fade", 60)}><img src="{logo_src(t["wordmark_en" if lang == "en" else "wordmark"])}" '
          f'alt="{"D-Robotics" if lang == "en" else "地瓜机器人"}"><i class="sc-sep"></i><span class="sc-ser">{esc(ser)}</span></div>')
    o += f'<div class="sc-badge"{a("pop", 140)}>{esc(badge(s))}</div>'
    o += '<div class="sc-txt">'
    o += f'<div class="sc-lab sc-fit"{a("left", 160)}>{lab}</div>'
    o += f'<h1 class="sc-title sc-fit"{a("rise", 240)}>{_title_html(s)}</h1>'
    o += f'<i class="sc-rule"{a("draw", 400)}></i>'
    if s.get('subtitle'):
        o += f'<p class="sc-sub sc-fit"{a("rise", 420)}>{esc(str(s["subtitle"]))}</p>'
    o += '</div>'
    if vis_html:
        o += f'<div class="sc-vis"{a("pop", 300)}>{vis_html}</div>'
    if s.get('mock'):
        o += f'<div class="sc-mock">{esc(L["mock"])}</div>'
    # the cover's own fields, so extract_spec.py can recover the spec from a built deck
    keep = {k: v for k, v in s.items() if k in FIELDS}
    o += ('<script type="application/json" class="sc-spec">'
          + json.dumps(keep, ensure_ascii=False).replace('</', '<\\/') + '</script>')
    return o + '</div>'


def css(themes=('light',)):
    """Stylesheet for the layout; only the themes actually used are emitted."""
    o = [f"""/* ---------------- series-cover (RDK 小课堂 series cover; scripts/series_cover.py) ---------------- */
.sc{{position:absolute;inset:0;font-family:{SANS}}}
.sc-bg .sc-panel{{position:absolute;left:960px;top:0;width:960px;height:1080px;background-size:36px 36px;
  -webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 30%,#000 100%);mask-image:linear-gradient(90deg,transparent 0%,#000 30%,#000 100%)}}
.sc-bg .sc-glow{{position:absolute;left:1060px;top:180px;width:720px;height:720px;border-radius:50%}}
.sc-lock{{position:absolute;left:280px;top:96px;display:flex;align-items:center;gap:28px;height:68px}}
.sc-lock img{{height:62px;width:auto;display:block}}
.sc-lock .sc-sep{{width:3px;height:52px}}
.sc-lock .sc-ser{{font:700 50px/1 {CJK};letter-spacing:3px}}
.sc-badge{{position:absolute;right:280px;top:96px;height:68px;display:flex;align-items:center;padding:0 30px;border-radius:16px;
  font:800 46px/1 {SANS};letter-spacing:1px}}
.sc-txt{{position:absolute;left:280px;top:0;bottom:0;width:{TEXT_W}px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;padding-top:40px}}
.sc-lab{{display:flex;align-items:center;gap:22px;font:700 50px/1 {SANS};white-space:nowrap}}
.sc-lab .sc-ls{{width:14px;height:56px;border-radius:7px;flex:none}}
.sc-title{{margin-top:34px;font:700 200px/1.04 {SANS};letter-spacing:4px;white-space:nowrap}}
.sc-title em{{font-style:normal;font-weight:800}}
.sc-rule{{display:block;margin-top:40px;width:120px;height:10px;border-radius:5px;transform-origin:left center}}
.sc-sub{{margin-top:34px;font:700 54px/1.25 {CJK};white-space:nowrap}}
.sc-vis{{position:absolute;left:{VIS_X}px;top:{540 - VIS_SIZE // 2 + 30}px;width:{VIS_SIZE}px;height:{VIS_SIZE}px}}
.sc-vis svg,.sc-vis img{{width:100%;height:100%;display:block;object-fit:contain}}
.sc-mock{{position:absolute;left:0;right:0;bottom:0;height:96px;background:#D93025;color:#fff;font:700 48px/96px {CJK};text-align:center;letter-spacing:4px;z-index:20}}
.sc-en .sc-lock img{{height:56px}}
.sc-en .sc-lock .sc-ser{{font:700 52px/1 {SANS};letter-spacing:.5px}}
.sc-en .sc-lab{{font:600 46px/1 {SANS};gap:18px}}
.sc-en .sc-title{{font:700 184px/1.0 {SANS};letter-spacing:0}}
.sc-en .sc-title em{{font-weight:800}}
.sc-en .sc-sub{{font:600 54px/1.25 {SANS};letter-spacing:0}}
.sc-en .sc-mock{{font-family:{SANS}}}
"""]
    for name in themes:
        t = THEMES[name]
        k = f'.sc-{name}'
        o.append(f"""{k} .sc-bg{{background:{t["bg"]}}}
{k} .sc-panel{{background-image:radial-gradient({t["line"]} 2.2px,transparent 2.6px)}}
{k} .sc-glow{{background:radial-gradient(circle,{t["glow"]} 0%,rgba(0,0,0,0) 68%)}}
{k},{k} .sc-title,{k} .sc-ser{{color:{t["ink"]}}}
{k} .sc-sep{{background:{t["line"]}}}
{k} .sc-badge{{background:{t["tag_bg"]};color:{t["tag_ink"]}}}
{k} .sc-lab,{k} .sc-sub{{color:{t["ink2"]}}}
{k} .sc-lab .sc-ls,{k} .sc-rule{{background:{t["stroke"]}}}
{k} .sc-lab .sc-ln,{k} .sc-title em{{color:{t["title_accent"]}}}
{k} .sc-lab .sc-dot{{color:{t["ink3"]}}}
{k} .sc-vis{{filter:drop-shadow(0 30px 50px rgba(0,0,0,{t["shadow"]}))}}
""")
    return ''.join(o)


# Shrink-to-fit (title, subtitle, chapter line never run past the 760px text column). Runs at load and again once the
# web fonts are ready; if a size changed while the cover was entering, the entrance is restarted so it plays in full.
JS = r"""(() => {
  const fitAll = () => { let changed = false;
    document.querySelectorAll('.sc .sc-fit').forEach(e => { e.style.fontSize = '';
      let fs = parseFloat(getComputedStyle(e).fontSize); const max = e.parentElement.clientWidth;
      while (e.scrollWidth > max && fs > 30) { fs -= 2; e.style.fontSize = fs + 'px'; }
      if (e.dataset.fs !== String(fs)) { e.dataset.fs = fs; changed = true; } });
    return changed; };
  fitAll();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => {
    if (!fitAll()) return;
    document.querySelectorAll('.slide.in .sc').forEach(sc => { const s = sc.closest('.slide');
      if (!document.documentElement.classList.contains('static')) { s.classList.remove('in'); void s.offsetWidth; s.classList.add('in'); } });
  });
})();
"""
