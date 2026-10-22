#!/usr/bin/env python3
"""dg-deck render: HTML deck -> per-slide PNGs (?static=1, 1920x1080) + numbered contact sheet
+ optional PDF (?print=1) + basic overflow check.

usage: render.py deck.html [-o OUTDIR] [--sheet FILE] [--cols 4] [--pdf FILE] [--no-png]
                           [--chrome PATH] [--scale 1]
Needs: playwright and Pillow. Uses --chrome, $CHROME, a system Chrome/Chromium,
or the browser from `playwright install chromium`.
Exit code 2 if the overflow check finds problems.
"""
import argparse, json, os, pathlib, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium, resolve_chrome

CHECK_JS = r"""
(i) => {
  const s = document.querySelectorAll('.slide')[i], sr = s.getBoundingClientRect(), out = [];
  const desc = e => e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).join('.') : '')
                    + ' "' + (e.textContent || '').trim().slice(0, 30) + '"';
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; };
  const skip = e => e.closest('.bg,.blob,.notes,svg.ring');
  for (const e of s.querySelectorAll('*')) {
    if (skip(e) || !vis(e)) continue;
    const r = e.getBoundingClientRect();
    if (r.right > sr.right + 1 || r.bottom > sr.bottom + 1 || r.left < sr.left - 1 || r.top < sr.top - 1)
      out.push(['off-slide', desc(e)]);
  }
  for (const e of s.querySelectorAll('.sc .sc-fit'))   // series-cover: text that could not shrink into its column
    if (e.scrollWidth > e.parentElement.clientWidth + 2) out.push(['overflow', desc(e)]);
  for (const b of s.querySelectorAll('.content,.card,.term,.tbody,.lk,.nl,.cl-card,.blist,table.tb,.bars,.note,.fs,.sec-left,.cv-left,.split,.cl')) {
    if (b.scrollHeight > b.clientHeight + 2 || b.scrollWidth > b.clientWidth + 2)
      out.push(['overflow', desc(b), `scroll ${b.scrollWidth}x${b.scrollHeight} > box ${b.clientWidth}x${b.clientHeight}`]);
  }
  for (const b of s.querySelectorAll('.card,.term,.lk,.nl,.cl-card,.blist,.bars,table.tb')) {
    const br = b.getBoundingClientRect();
    for (const c of b.querySelectorAll('*')) { if (!vis(c) || c.closest('.ln.hlt') && c !== c.closest('.ln')) continue;
      const r = c.getBoundingClientRect();
      if (r.right > br.right + 1 || r.bottom > br.bottom + 1) { out.push(['escapes-box', desc(c), 'in ' + desc(b)]); break; } }
  }
  const foot = s.querySelector('.foot');
  if (foot) { const fr = foot.getBoundingClientRect();
    for (const c of s.querySelectorAll('.content > *, .split > *')) if (c.getBoundingClientRect().bottom > fr.top - 4) out.push(['hits-footer', desc(c)]); }
  for (const e of s.querySelectorAll('*')) {
    if (skip(e)) continue;
    const cs = getComputedStyle(e);
    if (cs.textOverflow === 'ellipsis' && e.scrollWidth > e.clientWidth + 1) out.push(['truncated', desc(e)]);
  }
  return {layout: s.dataset.layout, title: s.dataset.title, issues: out};
}
"""


def contact_sheet(pngs, labels, path, cols=4, tw=480):
    from PIL import Image, ImageDraw, ImageFont
    th, pad, lab = tw * 9 // 16, 16, 34
    rows = (len(pngs) + cols - 1) // cols
    W, H = cols * tw + (cols + 1) * pad, rows * (th + lab) + (rows + 1) * pad
    sheet = Image.new('RGB', (W, H), (218, 220, 224))
    font = None
    for fp, idx in (('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 2),
                    ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 0),
                    ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 0),
                    ('DejaVuSans.ttf', 0)):
        try:
            font = ImageFont.truetype(fp, 20, index=idx); break
        except Exception:
            pass
    dr = ImageDraw.Draw(sheet)
    for k, (p, l) in enumerate(zip(pngs, labels)):
        r, c = divmod(k, cols)
        x, y = pad + c * (tw + pad), pad + r * (th + lab + pad)
        im = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (x, y + lab))
        dr.rounded_rectangle((x, y + 2, x + 44, y + lab - 4), 6, fill=(255, 90, 0))
        dr.text((x + 22, y + lab // 2 - 1), f'{k + 1:02d}', fill='white', font=font, anchor='mm')
        dr.text((x + 54, y + lab // 2 - 1), l, fill=(32, 33, 36), font=font, anchor='lm')
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html')
    ap.add_argument('-o', '--outdir', help='per-slide PNG dir (default: <html dir>/png)')
    ap.add_argument('--sheet', help='contact sheet path (default: <outdir>/../contact_sheet.png)')
    ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--pdf', help='also write a PDF via ?print=1')
    ap.add_argument('--no-png', action='store_true')
    ap.add_argument('--prefix', default='slide-')
    ap.add_argument('--scale', type=float, default=1.0, help='device scale factor for PNGs')
    ap.add_argument('--chrome', default=None, help='Chrome/Chromium executable (else $CHROME, a system Chrome, or Playwright Chromium)')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    chrome = resolve_chrome(a.chrome)
    src = pathlib.Path(a.html).resolve()
    outdir = pathlib.Path(a.outdir or src.parent / 'png')
    sheet = pathlib.Path(a.sheet or outdir.parent / 'contact_sheet.png')
    report, bad = [], 0
    with sync_playwright() as p:
        br = launch_chromium(p, chrome, ['--hide-scrollbars'])
        if not a.no_png:
            outdir.mkdir(parents=True, exist_ok=True)
            pg = br.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=a.scale)
            pg.goto(src.as_uri() + '?static=1&export=1#1')
            pg.evaluate('document.fonts.ready')
            n = pg.evaluate('DG.count')
            pngs, labels = [], []
            for i in range(n):
                pg.evaluate(f'DG.show({i})')
                pg.wait_for_timeout(60)
                f = outdir / f'{a.prefix}{i + 1:02d}.png'
                pg.screenshot(path=str(f))
                r = pg.evaluate(CHECK_JS, i)
                pngs.append(f); labels.append(f'{r["layout"]} · {r["title"]}')
                report.append({'slide': i + 1, **r})
                if r['issues']:
                    bad += 1
            contact_sheet(pngs, labels, sheet, a.cols)
            print(f'{n} PNGs -> {outdir}/  contact sheet -> {sheet}')
            for r in report:
                for it in r['issues']:
                    print(f'  ! slide {r["slide"]:02d} [{r["layout"]}] ' + ' | '.join(map(str, it)))
            print('overflow check: ' + ('OK, no issues' if not bad else f'{bad} slide(s) with issues'))
            (sheet.parent / (sheet.stem + '.overflow.json')).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
        if a.pdf:
            pg = br.new_page(viewport={'width': 1920, 'height': 1080})
            pg.goto(src.as_uri() + '?print=1')
            pg.evaluate('document.fonts.ready')
            pg.pdf(path=a.pdf, width='1920px', height='1080px', print_background=True, prefer_css_page_size=True)
            print(f'PDF -> {a.pdf}')
        br.close()
    sys.exit(2 if bad else 0)


if __name__ == '__main__':
    main()
