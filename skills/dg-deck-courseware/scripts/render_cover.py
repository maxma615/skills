#!/usr/bin/env python3
"""dg-deck render_cover: platform thumbnail (video cover) from the SAME template and fields as slide 1.

The thumbnail is the deck's `series-cover` slide rendered on its own: this script builds a one-slide deck
with build.py (layout `series-cover`, scripts/series_cover.py) and screenshots its final frame. A deck's
slide 1 and its video cover therefore never drift apart.

usage:
  # from the deck spec (uses its series-cover slide + meta.lang) -- preferred
  render_cover.py --spec lesson.json -o publish/cover.png [--thumbs]

  # from fields
  render_cover.py --chapter 2 --chapter-name "Model Zoo" --lesson 1 --title "认识 BPU" \
      --highlight BPU --subtitle "为什么要先转换 + 量化才能上板" --visual bpu -o cover.png
  render_cover.py --lang en --chapter 2 --chapter-name "Model Zoo" --lesson 1 --title "Meet the\\nBPU" \
      --highlight BPU --subtitle "Why convert + quantize first?" --visual bpu -o cover_en.png

  --theme    light (default, the series style) | dark | orange
  --visual   bpu | quant (built-in key visuals) or an image path; --visual none for no visual
  --mock     stamp a "MOCK-UP" bar (template previews only)
  --thumbs   also write 320x180 and 240x180 (4:3) previews for a small-size readability check
  --html     keep the generated one-slide deck HTML at this path

Writes <out>.png (1920x1080) and <out>_4x3.png (1440x1080 centre crop, x=240..1680). Key content must stay
inside that 4:3 safe area; the script warns (exit 2) if it does not, or if any text overflows.
Needs: playwright and Pillow (same as render.py).
"""
import argparse, json, os, pathlib, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B
import series_cover as SC
from browser import launch_chromium, resolve_chrome

SAFE_X0, SAFE_X1 = 240, 1680
CHECK = f'''() => {{ const out = [];
  for (const e of document.querySelectorAll('.slide.active .sc-lock,.slide.active .sc-badge,.slide.active .sc-fit,.slide.active .sc-vis')) {{
    const r = e.getBoundingClientRect(), w = Math.max(r.width, e.scrollWidth);
    if (r.left < {SAFE_X0} || r.left + w > {SAFE_X1}) out.push('outside 4:3 safe area: ' + e.className);
    if (e.classList.contains('sc-fit') && e.scrollWidth > e.parentElement.clientWidth + 1) out.push('overflows text column: ' + e.className);
  }} return out; }}'''


def spec_from_args(a):
    if a.spec:
        deck = json.loads(pathlib.Path(a.spec).read_text(encoding='utf-8'))
        covers = [s for s in deck['slides'] if s.get('layout') == 'series-cover']
        if not covers:
            sys.exit(f'{a.spec}: no series-cover slide')
        s = dict(covers[0]); meta = dict(deck.get('meta', {}))
        base = os.path.dirname(os.path.abspath(a.spec))
    else:
        missing = [k for k in ('chapter', 'chapter_name', 'lesson', 'title') if getattr(a, k) is None]
        if missing:
            sys.exit('missing: ' + ', '.join('--' + m.replace('_', '-') for m in missing) + ' (or use --spec)')
        s = {'layout': 'series-cover', 'chapter': a.chapter, 'chapter_name': a.chapter_name, 'lesson': a.lesson,
             'title': a.title.replace('\\n', '\n')}
        for k in ('highlight', 'subtitle', 'series', 'badge'):
            if getattr(a, k):
                s[k] = getattr(a, k)
        meta = {'lang': 'en' if a.lang == 'en' else 'zh-CN'}
        base = os.getcwd()
    for k in ('theme', 'visual'):
        if getattr(a, k):
            s[k] = getattr(a, k)
    if s.get('visual') == 'none':
        s['visual'] = ''
    if a.mock:
        s['mock'] = True
    s.pop('notes', None)
    meta.setdefault('footer', '')
    return {'meta': meta, 'slides': [s]}, base


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--spec', help='deck spec JSON; its series-cover slide and meta.lang are used')
    ap.add_argument('--chapter', type=int); ap.add_argument('--chapter-name'); ap.add_argument('--lesson', type=int)
    ap.add_argument('--title'); ap.add_argument('--highlight', '--accent', dest='highlight'); ap.add_argument('--subtitle')
    ap.add_argument('--visual'); ap.add_argument('--theme', choices=tuple(SC.THEMES))
    ap.add_argument('--lang', default='zh', choices=('zh', 'en')); ap.add_argument('--series'); ap.add_argument('--badge')
    ap.add_argument('--mock', action='store_true'); ap.add_argument('--thumbs', action='store_true')
    ap.add_argument('--html', help='keep the one-slide deck HTML here')
    ap.add_argument('--chrome', default=None, help='Chrome/Chromium executable (else $CHROME, a system Chrome, or Playwright Chromium)')
    ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    from PIL import Image
    from playwright.sync_api import sync_playwright

    spec, base = spec_from_args(a)
    page = B.build(spec, log=lambda *x: None, base_dir=base)
    out = pathlib.Path(a.out).with_suffix(''); out.parent.mkdir(parents=True, exist_ok=True)
    html = pathlib.Path(a.html) if a.html else out.parent / f'.{out.name}.html'
    html.write_text(page, encoding='utf-8')
    with sync_playwright() as p:
        br = launch_chromium(p, resolve_chrome(a.chrome), ['--hide-scrollbars'])
        pg = br.new_page(viewport={'width': 1920, 'height': 1080})
        pg.goto(html.resolve().as_uri() + '?static=1&export=1#1')
        pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
        issues = pg.evaluate(CHECK)
        pg.screenshot(path=f'{out}.png'); br.close()
    if not a.html:
        html.unlink()
    im = Image.open(f'{out}.png').convert('RGB'); im.save(f'{out}.png', optimize=True)
    c = im.crop((SAFE_X0, 0, SAFE_X1, 1080)); c.save(f'{out}_4x3.png', optimize=True)
    if a.thumbs:
        im.resize((320, 180), Image.LANCZOS).save(f'{out}_thumb320.png')
        c.resize((240, 180), Image.LANCZOS).save(f'{out}_4x3_thumb240.png')
    print(f'{out}.png  {out}_4x3.png' + ('  (+ thumbs)' if a.thumbs else ''))
    print('title: ' + SC.series_title(spec['slides'][0], spec['meta']))
    for i in issues:
        print('  ! ' + i)
    sys.exit(2 if issues else 0)


if __name__ == '__main__':
    main()
