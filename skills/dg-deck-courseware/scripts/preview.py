#!/usr/bin/env python3
"""Record MP4 previews of animated slides (deck mode, ?export=1) with playwright video + ffmpeg.
usage: preview.py deck.html -o OUTDIR [--slides 6,7,8] [--size 1280x720] [--chrome PATH]
Also writes <name>.frames.jpg (1 frame/s contact strip) for review.
Default slides: every slide with data-layout=diagram.
Uses --chrome, $CHROME, a system Chrome/Chromium, or `playwright install chromium`."""
import argparse, os, pathlib, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium, resolve_chrome
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('html'); ap.add_argument('-o', '--outdir', required=True)
ap.add_argument('--slides', help='1-based list; default: every slide with data-layout=diagram')
ap.add_argument('--size', default='1280x720')
ap.add_argument('--chrome', default=None, help='Chrome/Chromium executable (else $CHROME, a system Chrome, or Playwright Chromium)')
a = ap.parse_args()
W, H = map(int, a.size.split('x'))
src = pathlib.Path(a.html).resolve(); out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
chrome = resolve_chrome(a.chrome)
with sync_playwright() as p:
    br = launch_chromium(p, chrome)
    pg = br.new_page(); pg.goto(src.as_uri() + '?static=1')
    info = pg.evaluate("""() => [...document.querySelectorAll('.slide')].map((s, i) => {
        const t = s.querySelector('script.dgm-tl'); const j = t ? JSON.parse(t.textContent) : null;
        return {n: i + 1, layout: s.dataset.layout, title: s.dataset.title, ms: j ? j.delay + j.end : 3000}; })""")
    pg.close()
    want = [int(x) for x in a.slides.split(',')] if a.slides else [x['n'] for x in info if x['layout'] == 'diagram']
    for n in want:
        it = info[n - 1]
        tmp = tempfile.mkdtemp()
        ctx = br.new_context(viewport={'width': W, 'height': H}, record_video_dir=tmp, record_video_size={'width': W, 'height': H})
        pg = ctx.new_page(); pg.goto(src.as_uri() + f'?export=1#{n}'); pg.evaluate('document.fonts.ready')
        pg.evaluate(f'(()=>{{const s=document.querySelectorAll(".slide")[{n - 1}]; s._dgm && s._dgm.play();}})()')   # restart after fonts are ready
        pg.wait_for_timeout(it['ms'] + 1200)
        vid = pg.video.path(); ctx.close()
        name = f'slide-{n:02d}-{it["title"]}'
        mp4 = out / f'{name}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-ss', '0.4', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24',
                        '-movflags', '+faststart', '-r', '25', str(mp4)], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp4), '-vf', 'fps=1,scale=480:-1,tile=5x4', '-frames:v', '1',
                        str(out / f'{name}.frames.jpg')], check=True)
        shutil.rmtree(tmp, ignore_errors=True)
        print(f'slide {n:02d} {it["title"]}: {mp4} ({it["ms"] / 1000:.1f}s timeline)')
    br.close()
