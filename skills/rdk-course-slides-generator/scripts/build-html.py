#!/usr/bin/env python3
"""
build-html.py — 把 blueprint JSON 渲染成 Apple 风视频演示 HTML。

用法:
    python3 build-html.py \\
        --blueprint <path>.json \\
        --lang cn|en \\
        --output <path>.html \\
        [--assets-dir <dir>]

blueprint JSON schema 见 references/slide-patterns.md 顶层 schema。
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import sys
from pathlib import Path


# ---------- Lucide SVG 图标库（从 references/icon-vocabulary.md 提取） ----------

ICONS = {
    "zap": '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>',
    "flask": '<path d="M9 3h6"/><path d="M10 3v7.5L4.9 19.1A2 2 0 0 0 6.6 22h10.8a2 2 0 0 0 1.7-2.9L14 10.5V3"/>',
    "gradcap": '<path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>',
    "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-6 4 6 4V8z"/>',
    "book-open": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
    "code": '<path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/>',
    "layers": '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>',
    "rocket": '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    "film": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 12h20"/><path d="M6 4v16M18 4v16M2 8h4M2 16h4M18 8h4M18 16h4"/>',
    "chip": '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "brain": '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="18" r="2.5"/><circle cx="19" cy="18" r="2.5"/><path d="M12 7.5v2.5M11 11c-1.6 1-3.7 2.6-5 5M13 11c1.6 1 3.7 2.6 5 5"/>',
    "robot": '<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M12 4v4"/><circle cx="12" cy="3" r="1"/><circle cx="8.5" cy="14" r="1"/><circle cx="15.5" cy="14" r="1"/><path d="M9 17h6"/><path d="M3 14H1M23 14h-2"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    "message": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "eye": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "arm": '<path d="M12 3v9"/><path d="M12 3l4 3M12 3l-4 3"/><path d="M9 12h6l2 3v4a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2v-4z"/><path d="M9 17h6"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2" fill="currentColor"/>',
    "star": '<circle cx="12" cy="9" r="6"/><path d="M8.5 13.5L7 22l5-3 5 3-1.5-8.5"/>',
    "puzzle": '<path d="M4 4h6v3.5a1.5 1.5 0 1 0 3 0V4h6v6h-3.5a1.5 1.5 0 1 0 0 3H20v6h-6v-3.5a1.5 1.5 0 1 0-3 0V20H4v-6h3.5a1.5 1.5 0 1 0 0-3H4z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 3 4 6 4 9s-1.5 6-4 9c-2.5-3-4-6-4-9s1.5-6 4-9z"/>',
    "github": '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.4 3.4 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.4 13.4 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>',
    "grid": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 3v18M16 3v18M3 8h18M3 16h18"/>',
    "terminal": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8l4 4-4 4"/><path d="M12 16h6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>',
    "list-check": '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6l2 2 3-3M3 12l2 2 3-3M3 18l2 2 3-3"/>',
}


def svg(icon_key: str) -> str:
    """把图标 key 渲染为完整 SVG 元素"""
    inner = ICONS.get(icon_key)
    if inner is None:
        # 兜底：如果 key 未定义，用一个空心方块提示（视觉上明显能看出图标缺失）
        inner = '<rect x="4" y="4" width="16" height="16" rx="2"/>'
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        + inner + '</svg>'
    )


# ---------- 样式常量 ----------

FONT_STACK_SANS = (
    '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", '
    '"PingFang SC", "HarmonyOS Sans SC", "MiSans", '
    '"Microsoft YaHei UI", "Microsoft YaHei", "Myriad Pro", sans-serif'
)
FONT_STACK_MONO = 'ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace'


def build_css(lang: str) -> str:
    """按语言返回完整 <style> 内容。"""
    # 字号档
    if lang == "cn":
        H1 = "clamp(40px, 4.8vw, 78px)"
        H2 = "clamp(34px, 3.8vw, 58px)"
        H3 = "clamp(19px, 1.6vw, 27px)"
        P  = "clamp(16px, 1.2vw, 21px)"
        LEAD = "clamp(19px, 1.5vw, 27px)"
        KICKER = "13px"
        KICKER_SPACING = ".18em"
        H2_WRAP = "nowrap"
        CARD_PAD = "22px"
        CARD_THEMED_PAD = "24px 22px 20px"
        ICON_PILL = "48px"
        ICON_SVG  = "24px"
        TIME_W, TIME_H, TIME_FS = "68px", "34px", "13px"
        CARD_P_FS = "clamp(15px, 1.05vw, 19px)"
        PATH_NO_FS = "40px"
        PATH_STRONG_FS = "19px"
        PATH_SPAN_FS = "14px"
        RESOURCE_STRONG_FS = "20px"
        RESOURCE_SPAN_FS = "15px"
        TAG_FS = "14px"
        TAG_PAD = "6px 11px"
        HERO_CENTER_SIZE = "200px"
        HERO_STRONG_FS = "42px"
        HERO_SPAN_FS = "16px"
        NODE_FS = "16px"
        NODE_PAD = "10px 14px"
        CHECKLIST_FS = "clamp(16px, 1.15vw, 20px)"
    else:  # en
        H1 = "clamp(40px, 4.6vw, 76px)"
        H2 = "clamp(32px, 3.4vw, 54px)"
        H3 = "clamp(19px, 1.55vw, 26px)"
        P  = "clamp(16px, 1.2vw, 20px)"
        LEAD = "clamp(18px, 1.45vw, 25px)"
        KICKER = "13px"
        KICKER_SPACING = ".16em"
        H2_WRAP = "normal"
        CARD_PAD = "22px"
        CARD_THEMED_PAD = "24px 22px 20px"
        ICON_PILL = "44px"
        ICON_SVG  = "22px"
        TIME_W, TIME_H, TIME_FS = "68px", "34px", "13px"
        CARD_P_FS = "clamp(15px, 1.05vw, 18px)"
        PATH_NO_FS = "38px"
        PATH_STRONG_FS = "19px"
        PATH_SPAN_FS = "14px"
        RESOURCE_STRONG_FS = "19px"
        RESOURCE_SPAN_FS = "14px"
        TAG_FS = "13px"
        TAG_PAD = "6px 11px"
        HERO_CENTER_SIZE = "180px"
        HERO_STRONG_FS = "38px"
        HERO_SPAN_FS = "14px"
        NODE_FS = "14px"
        NODE_PAD = "9px 14px"
        CHECKLIST_FS = "clamp(14px, 1.1vw, 18px)"

    return f"""
    :root {{
      /* === 地瓜品牌色板（官方规范）=== */
      --brand:  #FF3C00;   /* 核心标准色：RGB 255,60,0 · CMYK 0,87,94,0 */
      --brand2: #FF6200;   /* 品牌橙 2：RGB 255,98,0 · 黑客松渐变终点 */
      --brand3: #FF0900;   /* 品牌深红：RGB 255,9,0 · 全谱渐变起点 */
      --o1:     #FF5500;   /* 辅色 O1：RGB 255,85,0 */
      --o2:     #FF7300;   /* 辅色 O2：RGB 255,115,0 */
      --o3:     #FF8C00;   /* 辅色 O3：RGB 255,140,0 */
      --o4:     #FF9D00;   /* 辅色 O4：RGB 255,157,0 */
      --o5:     #FFAE00;   /* 辅色 O5：RGB 255,174,0 · 全谱渐变暖金终点 */
      /* === 灰阶与线条 === */
      --text: #111111;
      --muted: #6e6e73;
      --line: rgba(17, 17, 17, .10);
      --line2: rgba(255, 60, 0, .18);
      --shadow: 0 24px 70px rgba(0, 0, 0, .08);
      --soft-shadow: 0 10px 30px rgba(0, 0, 0, .06);
      /* === 字体 === */
      --font-sans: {FONT_STACK_SANS};
      --font-mono: {FONT_STACK_MONO};
      /* === 缓动 === */
      --ease-out-expo: cubic-bezier(0.22, 1, 0.36, 1);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ width: 100%; height: 100%; margin: 0; overflow: hidden; }}
    body {{
      font-family: var(--font-sans);
      font-weight: 400;
      font-variant-numeric: tabular-nums;
      font-feature-settings: "ss01", "ss02", "cv11";
      text-rendering: optimizeLegibility;
      background:
        radial-gradient(circle at 86% 10%, rgba(255, 60, 0, .13), transparent 30%),
        radial-gradient(circle at 8% 90%, rgba(255, 174, 0, .13), transparent 34%),
        linear-gradient(135deg, #ffffff 0%, #f8f7f4 44%, #f2f1ee 100%);
      color: var(--text);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}
    body::before {{
      content: ""; position: fixed; inset: 0;
      background:
        linear-gradient(90deg, rgba(0,0,0,.035) 1px, transparent 1px),
        linear-gradient(rgba(0,0,0,.03) 1px, transparent 1px);
      background-size: 64px 64px;
      mask-image: radial-gradient(circle at center, rgba(0,0,0,.52), transparent 72%);
      pointer-events: none;
    }}
    body::after {{
      content: ""; position: fixed; right: -14vw; top: -18vh;
      width: 52vw; height: 52vw; border-radius: 50%;
      background: radial-gradient(circle, rgba(255,98,0,.20), rgba(255,9,0,.08) 38%, transparent 66%);
      filter: blur(4px); pointer-events: none;
    }}
    .brand-logo {{
      position: fixed; right: 34px; top: 24px; z-index: 20;
      height: 44px; width: auto; object-fit: contain; object-position: right center;
      pointer-events: none; filter: drop-shadow(0 6px 14px rgba(0, 0, 0, .08));
    }}
    .deck {{ width: 100vw; height: 100vh; position: relative; }}
    .slide {{
      position: absolute; inset: 0; padding: 5.2vh 6vw;
      display: none; opacity: 0;
      transform: translateY(28px) scale(.985); filter: blur(4px);
      transition: opacity .8s var(--ease-out-expo), transform .8s var(--ease-out-expo), filter .6s var(--ease-out-expo);
      will-change: opacity, transform, filter;
    }}
    .slide.active {{ display: flex; opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }}
    .slide.leaving {{
      display: flex; opacity: 0; transform: translateY(-24px) scale(.985); filter: blur(4px);
      transition: opacity .38s var(--ease-out-expo), transform .38s var(--ease-out-expo), filter .38s var(--ease-out-expo);
    }}
    .slide.active .slide-inner > * {{ animation: rise .9s var(--ease-out-expo) both; }}
    .slide.active .slide-inner > *:nth-child(1) {{ animation-delay: .08s; }}
    .slide.active .slide-inner > *:nth-child(2) {{ animation-delay: .18s; }}
    .slide.active .slide-inner > *:nth-child(3) {{ animation-delay: .28s; }}
    .slide.active .slide-inner > *:nth-child(4) {{ animation-delay: .38s; }}
    .slide.active .slide-inner > *:nth-child(5) {{ animation-delay: .48s; }}
    .slide.active .grid > *, .slide.active .path > *,
    .slide.active .checklist > li, .slide.active .timeline > *,
    .slide.active .flow > * {{
      animation: rise-sub .8s var(--ease-out-expo) both;
    }}
    .slide.active .grid > *:nth-child(1), .slide.active .path > *:nth-child(1),
    .slide.active .checklist > li:nth-child(1), .slide.active .timeline > *:nth-child(1),
    .slide.active .flow > *:nth-child(1) {{ animation-delay: .28s; }}
    .slide.active .grid > *:nth-child(2), .slide.active .path > *:nth-child(2),
    .slide.active .checklist > li:nth-child(2), .slide.active .timeline > *:nth-child(2),
    .slide.active .flow > *:nth-child(2) {{ animation-delay: .36s; }}
    .slide.active .grid > *:nth-child(3), .slide.active .path > *:nth-child(3),
    .slide.active .checklist > li:nth-child(3), .slide.active .timeline > *:nth-child(3),
    .slide.active .flow > *:nth-child(3) {{ animation-delay: .44s; }}
    .slide.active .grid > *:nth-child(4), .slide.active .path > *:nth-child(4),
    .slide.active .checklist > li:nth-child(4), .slide.active .timeline > *:nth-child(4),
    .slide.active .flow > *:nth-child(4) {{ animation-delay: .52s; }}
    .slide.active .grid > *:nth-child(5), .slide.active .path > *:nth-child(5),
    .slide.active .flow > *:nth-child(5) {{ animation-delay: .60s; }}
    .slide.active .grid > *:nth-child(6), .slide.active .path > *:nth-child(6) {{ animation-delay: .68s; }}
    .slide.active .grid > *:nth-child(7) {{ animation-delay: .76s; }}
    .slide.active .grid > *:nth-child(8) {{ animation-delay: .84s; }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes rise-sub {{ from {{ opacity: 0; transform: translateY(14px) scale(.985); }} to {{ opacity: 1; transform: translateY(0) scale(1); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .slide, .slide.leaving {{ transition-duration: .12s; filter: none; transform: none; }}
      .slide.active * {{ animation: none !important; }}
    }}
    .slide-inner {{
      position: relative; width: min(1600px, 100%); height: min(900px, 100%);
      margin: auto; display: flex; flex-direction: column; justify-content: center; gap: 26px; z-index: 1;
    }}
    .kicker {{
      display: inline-flex; align-items: center; gap: 10px;
      font-family: var(--font-sans);
      color: var(--brand); font-size: {KICKER}; letter-spacing: {KICKER_SPACING}; font-weight: 640;
      text-transform: uppercase;
    }}
    .kicker::before {{ content: ""; width: 32px; height: 2px; background: linear-gradient(90deg, var(--brand), rgba(255,60,0,0)); }}
    h1, h2, h3, p {{ margin: 0; }}
    h1, h2, h3 {{ font-family: var(--font-sans); color: #050505; text-wrap: balance; }}
    h1 {{ font-size: {H1}; line-height: 1.03; letter-spacing: -0.036em; font-weight: 720; white-space: nowrap; }}
    h2 {{ font-size: {H2}; line-height: 1.06; letter-spacing: -0.028em; font-weight: 720; white-space: {H2_WRAP}; }}
    h3 {{ font-size: {H3}; line-height: 1.24; letter-spacing: -0.012em; font-weight: 640; color: #111; }}
    p, li {{ font-size: {P}; line-height: 1.6; letter-spacing: -0.006em; color: var(--muted); }}
    .lead {{ font-size: {LEAD}; color: #333336; max-width: 1080px; line-height: 1.55; letter-spacing: -0.010em; font-weight: 400; text-wrap: pretty; }}
    .gradient {{ background: linear-gradient(90deg, var(--brand3), var(--brand), var(--brand2), var(--o5)); -webkit-background-clip: text; background-clip: text; color: transparent; }}
    .grid {{ display: grid; gap: 20px; }}
    .cols-2 {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .cols-3 {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .cols-4 {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .split {{ display: grid; grid-template-columns: 1.08fr .92fr; gap: 34px; align-items: center; }}
    .cover-split {{ grid-template-columns: minmax(0, 1.08fr) minmax(0, .92fr); }}
    .cover-split h1 {{ white-space: normal; }}
    .card {{ padding: {CARD_PAD}; border-radius: 28px; background: rgba(255,255,255,.78); border: 1px solid var(--line); min-height: 118px; box-shadow: var(--soft-shadow); backdrop-filter: blur(18px); }}
    .card h3 {{ margin-bottom: 10px; }}
    .card p, .card li {{ font-size: {CARD_P_FS}; line-height: 1.55; }}
    .card.themed {{ position: relative; padding: {CARD_THEMED_PAD}; overflow: hidden; border: 1px solid rgba(255,255,255,.9); }}
    .card.themed::before {{ content: ""; position: absolute; inset: 0; background: var(--tint, linear-gradient(135deg, rgba(255,255,255,.86), rgba(255,247,240,.72))); z-index: 0; }}
    .card.themed > * {{ position: relative; z-index: 1; }}
    .card.themed .card-icon {{ width: {ICON_PILL}; height: {ICON_PILL}; display: grid; place-items: center; border-radius: 14px; background: rgba(255,255,255,.9); border: 1px solid rgba(255,255,255,.9); box-shadow: 0 8px 22px rgba(255,60,0,.10), inset 0 0 0 1px rgba(0,0,0,.02); color: var(--accent); margin-bottom: 14px; }}
    .card.themed .card-icon svg {{ width: {ICON_SVG}; height: {ICON_SVG}; }}
    .card.themed h3 {{ color: var(--accent, var(--brand)); font-weight: 720; letter-spacing: -0.014em; margin-bottom: 8px; }}
    .card.themed p {{ color: #3a3a3d; }}
    .tint-1 {{ --tint: linear-gradient(135deg, rgba(255,68,0,.14), rgba(255,255,255,.6)); --accent: #E53500; }}
    .tint-2 {{ --tint: linear-gradient(135deg, rgba(255,140,0,.14), rgba(255,255,255,.6)); --accent: #C96500; }}
    .tint-3 {{ --tint: linear-gradient(135deg, rgba(255,196,0,.16), rgba(255,255,255,.6)); --accent: #A67200; }}
    .tint-4 {{ --tint: linear-gradient(135deg, rgba(112,196,255,.16), rgba(255,255,255,.6)); --accent: #0A6DBF; }}
    .tint-5 {{ --tint: linear-gradient(135deg, rgba(140,120,255,.14), rgba(255,255,255,.6)); --accent: #5A46C7; }}
    .tint-6 {{ --tint: linear-gradient(135deg, rgba(80,200,150,.14), rgba(255,255,255,.6)); --accent: #158961; }}
    .tag {{ display: inline-flex; align-items: center; padding: {TAG_PAD}; border: 1px solid rgba(255,60,0,.18); border-radius: 999px; background: rgba(255,60,0,.07); color: var(--brand); font-size: {TAG_FS}; font-weight: 700; margin: 4px 6px 4px 0; }}
    .hero-panel {{ position: relative; min-height: 480px; border-radius: 42px; background: rgba(255,255,255,.72); border: 1px solid rgba(255,255,255,.84); box-shadow: var(--shadow); overflow: hidden; backdrop-filter: blur(24px); }}
    .hero-panel::before {{ content: ""; position: absolute; inset: auto -80px -100px auto; width: 300px; height: 300px; border-radius: 50%; background: linear-gradient(135deg, rgba(255,98,0,.22), rgba(255,9,0,.08)); }}
    .hero-orbit {{ position: absolute; inset: 48px; border-radius: 50%; border: 1px solid rgba(255,60,0,.16); }}
    .hero-orbit.two {{ inset: 105px; border-color: rgba(255,174,0,.24); }}
    .hero-center {{ position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: {HERO_CENTER_SIZE}; height: {HERO_CENTER_SIZE}; border-radius: 50%; display: grid; place-items: center; text-align: center; background: linear-gradient(135deg, #fff, #fff2e9); border: 1px solid rgba(255,60,0,.18); box-shadow: 0 20px 60px rgba(255,60,0,.12); }}
    .hero-center strong {{ color: var(--brand); font-size: {HERO_STRONG_FS}; line-height: 1; letter-spacing: -0.03em; }}
    .hero-center span {{ color: var(--muted); font-size: {HERO_SPAN_FS}; }}
    .node {{ position: absolute; padding: {NODE_PAD}; border-radius: 16px; background: rgba(255,255,255,.90); border: 1px solid var(--line2); font-weight: 700; color: #1d1d1f; box-shadow: 0 10px 28px rgba(255,60,0,.10); font-size: {NODE_FS}; letter-spacing: -0.004em; }}
    .n1 {{ left: 54px; top: 76px; }}
    .n2 {{ right: 58px; top: 96px; }}
    .n3 {{ left: 70px; bottom: 92px; }}
    .n4 {{ right: 74px; bottom: 78px; }}
    .path {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; align-items: stretch; }}
    .path-step {{ position: relative; padding: 18px 16px; border-radius: 24px; background: rgba(255,255,255,.82); border: 1px solid var(--line); box-shadow: var(--soft-shadow); min-height: 150px; }}
    .path-step::before {{ content: attr(data-no); display: block; color: rgba(255,60,0,.22); font-size: {PATH_NO_FS}; line-height: 1; font-weight: 900; margin-bottom: 10px; }}
    .path-step strong {{ display: block; color: #111; font-size: {PATH_STRONG_FS}; line-height: 1.2; margin-bottom: 6px; font-weight: 720; }}
    .path-step span {{ color: var(--muted); font-size: {PATH_SPAN_FS}; line-height: 1.5; }}
    .resource {{ display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 18px 20px; border-radius: 24px; background: rgba(255,255,255,.82); border: 1px solid var(--line); box-shadow: var(--soft-shadow); }}
    .resource strong {{ font-size: {RESOURCE_STRONG_FS}; color: #111; font-weight: 720; letter-spacing: -0.01em; }}
    .resource span {{ color: var(--muted); font-size: {RESOURCE_SPAN_FS}; line-height: 1.5; }}
    a.btn {{ text-decoration: none; border: 1px solid rgba(255,60,0,.20); color: #fff; background: linear-gradient(135deg, var(--brand), var(--brand2)); padding: 10px 15px; border-radius: 999px; font-weight: 800; cursor: pointer; white-space: nowrap; box-shadow: 0 10px 24px rgba(255,60,0,.18); }}
    .timeline {{ display: grid; gap: 16px; }}
    .timeline-row {{ display: grid; grid-template-columns: {TIME_W} 1fr; gap: 22px; align-items: center; padding: 16px 20px; background: rgba(255,255,255,.72); border: 1px solid var(--line); border-radius: 20px; box-shadow: var(--soft-shadow); }}
    .timeline-row p {{ margin: 0; color: #202124; font-size: {P}; line-height: 1.5; letter-spacing: -0.006em; }}
    .time {{ display: inline-flex; align-items: center; justify-content: center; width: {TIME_W}; height: {TIME_H}; border-radius: 999px; background: linear-gradient(135deg, rgba(255,60,0,.10), rgba(255,174,0,.10)); border: 1px solid rgba(255,60,0,.18); color: var(--brand); font-weight: 700; font-size: {TIME_FS}; letter-spacing: .04em; }}
    .checklist {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; }}
    .checklist li {{ padding: 12px 16px 12px 44px; background: rgba(255,255,255,.82); border: 1px solid var(--line); border-radius: 18px; position: relative; box-shadow: var(--soft-shadow); font-size: {CHECKLIST_FS}; color: #202124; }}
    .checklist li::before {{ content: "✓"; position: absolute; left: 16px; top: 12px; color: var(--brand); font-weight: 900; }}
    .flow {{ display: flex; align-items: stretch; gap: 14px; flex-wrap: wrap; }}
    .step {{ flex: 1; min-width: 180px; padding: 21px; position: relative; border-radius: 22px; border: 1px solid var(--line); background: rgba(255,255,255,.82); box-shadow: var(--soft-shadow); }}
    .step:not(:last-child)::after {{ content: "→"; position: absolute; right: -18px; top: 50%; transform: translateY(-50%); color: var(--brand); font-size: 24px; z-index: 2; font-weight: 800; }}
    .step strong {{ display: block; font-size: {PATH_STRONG_FS}; margin-bottom: 6px; color: #111; font-weight: 720; letter-spacing: -0.01em; }}
    .step span {{ color: var(--muted); font-size: {PATH_SPAN_FS}; line-height: 1.5; }}
    .code {{ font-family: var(--font-mono); color: #111; background: #fff; border: 1px solid rgba(255,60,0,.16); padding: 14px 16px; border-radius: 16px; font-size: 17px; box-shadow: var(--soft-shadow); }}
    .bar {{ position: fixed; left: 28px; right: 28px; bottom: 22px; height: 4px; background: rgba(0,0,0,.08); border-radius: 99px; overflow: hidden; z-index: 10; }}
    .bar span {{ display: block; height: 100%; width: 0%; background: linear-gradient(90deg, var(--brand3), var(--brand), var(--brand2), var(--o5)); transition: width .25s ease; }}
    .nav {{ position: fixed; right: 28px; bottom: 38px; display: flex; gap: 10px; z-index: 10; align-items: center; }}
    .nav button {{ width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--line); background: rgba(255,255,255,.78); color: #111; font-size: 22px; cursor: pointer; box-shadow: var(--soft-shadow); }}
    .page {{ color: var(--muted); font-size: 15px; min-width: 68px; text-align: center; font-weight: 700; }}
    .hint {{ position: fixed; left: 28px; bottom: 38px; color: rgba(0,0,0,.42); font-size: 14px; z-index: 10; }}
    @media (max-width: 1200px) {{
      .path {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .cols-4, .cols-3 {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .split {{ grid-template-columns: 1fr; }}
      .hero-panel {{ min-height: 340px; }}
      .brand-logo {{ height: 34px; }}
      h1, h2 {{ white-space: normal; }}
    }}
    """


# ---------- Slide 渲染 ----------

def render_gradient(text: str) -> str:
    """把 [gradient]xxx[/gradient] 标记转成 <span class="gradient">xxx</span>"""
    return text.replace("[gradient]", '<span class="gradient">').replace("[/gradient]", "</span>")


def render_cover(slide, index) -> str:
    tags = slide.get("tags", [])
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
    nodes = slide.get("hero_nodes", [])
    node_positions = ["n1", "n2", "n3", "n4"]
    nodes_html = "".join(
        f'<div class="node {p}">{n}</div>'
        for p, n in zip(node_positions, nodes[:4])
    )
    center = slide.get("hero_center", {"strong": "RDK", "sub": ""})
    active = " active" if index == 0 else ""
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    lead = slide.get("lead", "")
    title_size = slide.get("title_size", "")
    title_style = f' style="white-space:nowrap;font-size:{title_size}"' if title_size else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Cover')}">
      <div class="slide-inner split cover-split">
        <div>
          <div class="kicker">{kicker}</div>
          <h1{title_style}>{title}</h1>
          <p class="lead">{lead}</p>
          <div>{tags_html}</div>
        </div>
        <div class="hero-panel">
          <div class="hero-orbit"></div><div class="hero-orbit two"></div>
          {nodes_html}
          <div class="hero-center"><div><strong>{center.get('strong','RDK')}</strong><br><span>{center.get('sub','')}</span></div></div>
        </div>
      </div>
    </section>"""


def render_cards_grid(slide, index, cols=3) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    lead_html = f'<p class="lead">{slide["lead"]}</p>' if slide.get("lead") else ""
    cards = slide.get("cards", [])
    cards_html = "\n          ".join(
        f'<div class="card themed {c.get("tint","tint-1")}">'
        f'<div class="card-icon">{svg(c.get("icon","zap"))}</div>'
        f'<h3>{c.get("title","")}</h3><p>{c.get("body","")}</p></div>'
        for c in cards
    )
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Cards')}">
      <div class="slide-inner">
        <div class="kicker">{kicker}</div>
        <h2>{title}</h2>
        {lead_html}
        <div class="grid cols-{cols}">
          {cards_html}
        </div>
      </div>
    </section>"""


def render_path_6(slide, index) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    steps = slide.get("steps", [])
    steps_html = "\n          ".join(
        f'<div class="path-step" data-no="{s.get("no","")}">'
        f'<strong>{s.get("title","")}</strong><span>{s.get("body","")}</span></div>'
        for s in steps[:6]
    )
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Path')}">
      <div class="slide-inner">
        <div class="kicker">{kicker}</div>
        <h2>{title}</h2>
        <div class="path">
          {steps_html}
        </div>
      </div>
    </section>"""


def render_split_checklist(slide, index) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    lead_html = f'<p class="lead">{slide["lead"]}</p>' if slide.get("lead") else ""
    items = slide.get("items", [])
    items_html = "\n          ".join(f'<li>{it}</li>' for it in items)
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Checklist')}">
      <div class="slide-inner split">
        <div>
          <div class="kicker">{kicker}</div>
          <h2>{title}</h2>
          {lead_html}
        </div>
        <ul class="checklist">
          {items_html}
        </ul>
      </div>
    </section>"""


def render_split_timeline(slide, index) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    lead_html = f'<p class="lead">{slide["lead"]}</p>' if slide.get("lead") else ""
    steps = slide.get("steps", [])
    steps_html = "\n          ".join(
        f'<div class="timeline-row"><div class="time">{s.get("badge","")}</div><p>{s.get("body","")}</p></div>'
        for s in steps
    )
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Timeline')}">
      <div class="slide-inner split">
        <div>
          <div class="kicker">{kicker}</div>
          <h2>{title}</h2>
          {lead_html}
        </div>
        <div class="timeline">
          {steps_html}
        </div>
      </div>
    </section>"""


def render_flow_5(slide, index) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    steps = slide.get("steps", [])
    steps_html = "\n          ".join(
        f'<div class="step"><strong>{s.get("title","")}</strong><span>{s.get("sub","")}</span></div>'
        for s in steps
    )
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Flow')}">
      <div class="slide-inner">
        <div class="kicker">{kicker}</div>
        <h2>{title}</h2>
        <div class="flow">
          {steps_html}
        </div>
      </div>
    </section>"""


def render_code_highlight(slide, index) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    lead_html = f'<p class="lead">{slide["lead"]}</p>' if slide.get("lead") else ""
    cards = slide.get("cards", [])
    cards_html_parts = []
    for c in cards:
        code = c.get("code", "")
        note = c.get("note", "")
        note_html = f'<p class="small" style="margin-top:10px;color:var(--muted)">{note}</p>' if note else ""
        cards_html_parts.append(
            f'<div class="card"><h3>{c.get("title","")}</h3>'
            f'<div class="code">{code}</div>{note_html}</div>'
        )
    cards_html = "\n          ".join(cards_html_parts)
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Debug')}">
      <div class="slide-inner">
        <div class="kicker">{kicker}</div>
        <h2>{title}</h2>
        {lead_html}
        <div class="grid cols-2">
          {cards_html}
        </div>
      </div>
    </section>"""


def render_resource_list(slide, index) -> str:
    kicker = slide.get("kicker", "")
    title = render_gradient(slide.get("title", ""))
    resources = slide.get("resources", [])
    open_label = slide.get("open_label", "Open")
    items_html = "\n          ".join(
        f'<div class="resource"><div><strong>{r["name"]}</strong><br><span>{r.get("desc","")}</span></div>'
        f'<a class="btn" target="_blank" href="{r.get("href","#")}">{open_label}</a></div>'
        for r in resources
    )
    active = " active" if index == 0 else ""
    return f"""    <section class="slide{active}" data-title="{slide.get('data_title', 'Resources')}">
      <div class="slide-inner">
        <div class="kicker">{kicker}</div>
        <h2>{title}</h2>
        <div class="grid cols-2">
          {items_html}
        </div>
      </div>
    </section>"""


def render_closing(slide, index) -> str:
    """跟 cards-3 类似，但语义上是收尾"""
    return render_cards_grid(slide, index, cols=slide.get("cols", 3))


PATTERN_MAP = {
    "cover": render_cover,
    "cards-3": lambda s, i: render_cards_grid(s, i, cols=3),
    "cards-4": lambda s, i: render_cards_grid(s, i, cols=4),
    "cards-6": lambda s, i: render_cards_grid(s, i, cols=3),
    "cards-8": lambda s, i: render_cards_grid(s, i, cols=4),
    "path-6": render_path_6,
    "split-checklist": render_split_checklist,
    "split-timeline": render_split_timeline,
    "flow-5": render_flow_5,
    "code-highlight": render_code_highlight,
    "resource-list": render_resource_list,
    "closing": render_closing,
}


def build_javascript() -> str:
    return """
  <script>
    const slides = [...document.querySelectorAll('.slide')];
    const page = document.getElementById('page');
    const progress = document.getElementById('progress');
    let index = -1;
    let transitioning = false;
    function show(nextIndex) {
      nextIndex = Math.max(0, Math.min(slides.length - 1, nextIndex));
      if (nextIndex === index && slides[index].classList.contains('active')) return;
      if (transitioning) return;
      const current = slides[index];
      if (current && current !== slides[nextIndex] && current.classList.contains('active')) {
        transitioning = true;
        current.classList.remove('active');
        current.classList.add('leaving');
        setTimeout(() => {
          current.classList.remove('leaving');
          slides.forEach((slide, i) => slide.classList.toggle('active', i === nextIndex));
          index = nextIndex;
          page.textContent = `${index + 1} / ${slides.length}`;
          progress.style.width = `${((index + 1) / slides.length) * 100}%`;
          transitioning = false;
        }, 320);
      } else {
        slides.forEach((slide, i) => slide.classList.toggle('active', i === nextIndex));
        index = nextIndex;
        page.textContent = `${index + 1} / ${slides.length}`;
        progress.style.width = `${((index + 1) / slides.length) * 100}%`;
      }
    }
    document.getElementById('prev').onclick = () => show(index - 1);
    document.getElementById('next').onclick = () => show(index + 1);
    window.addEventListener('keydown', event => {
      if (['ArrowRight', 'PageDown', ' '].includes(event.key)) { event.preventDefault(); show(index + 1); }
      if (['ArrowLeft', 'PageUp'].includes(event.key)) { event.preventDefault(); show(index - 1); }
      if (event.key === 'Home') show(0);
      if (event.key === 'End') show(slides.length - 1);
      if (/^[0-9]$/.test(event.key)) {
        const n = Number(event.key);
        if (n > 0 && n <= slides.length) show(n - 1);
      }
    });
    show(0);
  </script>
"""


def build_html(blueprint: dict, assets_dir: Path) -> str:
    meta = blueprint.get("meta", {})
    lang = meta.get("lang", "cn")
    logo_key = meta.get("logo_key", "logo-cn")
    title = meta.get("title", "RDK Course")
    hint = meta.get("hint", "键盘：← / → / Space 切换页面" if lang == "cn" else "Keyboard: ← / → / Space to navigate")

    # 加载 logo 并 base64 内嵌
    logo_path = assets_dir / f"{logo_key}.png"
    if not logo_path.exists():
        raise FileNotFoundError(f"Logo not found: {logo_path}")
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_uri = f"data:image/png;base64,{logo_b64}"

    # 渲染每张 slide
    slides = blueprint.get("slides", [])
    slides_html_parts = []
    for i, slide in enumerate(slides):
        pattern = slide.get("pattern", "cards-3")
        renderer = PATTERN_MAP.get(pattern)
        if renderer is None:
            raise ValueError(f"Unknown pattern: {pattern} in slide {i}")
        slides_html_parts.append(renderer(slide, i))
    slides_html = "\n\n".join(slides_html_parts)

    css = build_css(lang)
    js = build_javascript()

    html_lang = "zh-CN" if lang == "cn" else "en"
    logo_alt = "地瓜机器人" if lang == "cn" else "D-Robotics"

    return f"""<!doctype html>
<html lang="{html_lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>{css}
  </style>
</head>
<body>
  <img class="brand-logo" src="{logo_uri}" alt="{logo_alt}" />
  <main class="deck" id="deck">
{slides_html}
  </main>

  <div class="hint">{hint}</div>
  <div class="nav"><button id="prev">‹</button><span class="page" id="page"></span><button id="next">›</button></div>
  <div class="bar"><span id="progress"></span></div>
{js}
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Build Apple-style slide HTML from a blueprint JSON.")
    parser.add_argument("--blueprint", required=True, help="Path to blueprint JSON")
    parser.add_argument("--lang", choices=["cn", "en"], default=None, help="Override meta.lang")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--assets-dir", default=None, help="Assets dir (default: <script>/../assets)")
    args = parser.parse_args()

    bp_path = Path(args.blueprint).resolve()
    if not bp_path.exists():
        print(f"Blueprint not found: {bp_path}", file=sys.stderr)
        sys.exit(1)

    with open(bp_path, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    if args.lang:
        blueprint.setdefault("meta", {})["lang"] = args.lang
        # 自动切 logo
        blueprint["meta"]["logo_key"] = f"logo-{args.lang}"

    if args.assets_dir:
        assets_dir = Path(args.assets_dir).resolve()
    else:
        assets_dir = Path(__file__).resolve().parent.parent / "assets"

    html = build_html(blueprint, assets_dir)

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path}")
    print(f"  size: {size_kb:.1f} KB")
    print(f"  slides: {len(blueprint.get('slides', []))}")
    print(f"  lang: {blueprint.get('meta', {}).get('lang', 'cn')}")
    print(f"  logo: {blueprint.get('meta', {}).get('logo_key', 'logo-cn')}")


if __name__ == "__main__":
    main()
