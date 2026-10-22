#!/usr/bin/env python3
"""Keyboard, mode, and reduced-motion smoke test for a built dg-deck HTML file.

usage: smoke_test.py deck.html [more.html ...] [--chrome PATH]
Uses --chrome, $CHROME, a system Chrome/Chromium, or `playwright install chromium`.
"""
import argparse, os, pathlib, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium, resolve_chrome
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('html', nargs='+')
ap.add_argument('--chrome', default=None, help='Chrome/Chromium executable (else $CHROME, a system Chrome, or Playwright Chromium)')
a = ap.parse_args()
chrome = resolve_chrome(a.chrome)
print('chrome:', chrome or 'playwright-chromium')
with sync_playwright() as p:
    br = launch_chromium(p, chrome)
    for f in a.html:
        u = pathlib.Path(f).resolve().as_uri(); r = {}
        pg = br.new_page(viewport={'width': 1280, 'height': 720}); pg.goto(u); pg.wait_for_timeout(300)
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(250)
        r['next'] = pg.evaluate('DG.index'); r['anims_running'] = pg.evaluate('document.getAnimations().length')
        r['in'] = pg.evaluate("document.querySelectorAll('.slide')[1].classList.contains('in')")
        r['hash'] = pg.evaluate('location.hash')
        pg.keyboard.press('n'); r['notes'] = pg.evaluate("document.documentElement.classList.contains('notes-on') && document.getElementById('notes-panel').textContent.length>3")
        pg.keyboard.press('End'); r['end'] = pg.evaluate('DG.index') + 1
        pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(100); r['prev'] = pg.evaluate('DG.index') + 1
        pg = br.new_page(); pg.goto(u + '?mode=scroll'); r['scroll'] = pg.evaluate("[document.documentElement.classList.contains('mode-scroll'), document.querySelectorAll('.frame').length]")
        pg = br.new_page(); pg.goto(u + '?print=1'); r['print'] = pg.evaluate("[document.documentElement.className, document.getAnimations().length]")
        pg = br.new_page(reduced_motion='reduce'); pg.goto(u); r['reduced_motion_static'] = pg.evaluate("document.documentElement.classList.contains('static')")
        pg = br.new_page(); pg.goto(u + '?export=1'); r['export_ui_hidden'] = pg.evaluate("getComputedStyle(document.querySelector('.nav')).display")
        print(pathlib.Path(f).name, r)
    br.close()
