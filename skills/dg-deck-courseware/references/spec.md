# dg-deck spec format (JSON)

```json
{
  "meta": {
    "title": "RDK 小课堂｜第二章 第 1 课：认识 BPU",   // <title> + html[data-title]; document.title = "<slide title> · <meta.title>"
                                // optional when slide 1 is series-cover: defaults to the series title (see below)
    "lang": "zh-CN",            // html[lang]; also picks the viewer UI language (en* → English, else Chinese)
    "mode": "deck",             // html[data-mode] default mode: deck | scroll
    "tag": "RDK 小课堂 2-01",    // top-right tag on every slide
    "footer": "认识 BPU",        // footer left part: "<footer> · <b><slide.title></b>"
    "theme": {},                // token overrides → ":root{--dg-<k>:<v>;}"  e.g. {"accent":"#1A73E8"}
    "logo": "d-robotics-icon.png", "logo_dark": "d-robotics-icon-dark.png",      // assets/brand/ (optional)
    "logo_full": "d-robotics-logo-full.png",                                    // closing-slide logo (…-en.png for English)
    "ui": {}                    // optional viewer-string overrides: {"hint","prev","next","no_notes"}
  },
  "slides": [ { "layout": "cover", "title": "封面", "notes": "…", … }, … ]
}
```

## Common slide fields
| field | meaning |
|---|---|
| `layout` | one of the 18 layouts (references/layouts.md) |
| `title` | `data-title` (nav / document.title) **and** footer label. Not rendered as heading. |
| `eyebrow`, `heading`, `lead` | small orange kicker, H1 (`<h2 class="h1">`), grey lead paragraph (optional). A lead shifts content stagger from 330 → 420 ms. |
| `notes` | speaker notes → `<aside class="notes">`, shown in the N panel. Optional. |
| `foot` | `false` to drop the footer (default: on, except cover/section/closing/quote) |
| `bg` | `stage` (default; light grey + drifting orange/blue glows), `white` (cover default; + conic blob), `dark` |
| `dark` | `true` → `.slide.dark` token set + dark background (CSS original; not used in 2-01) |

## Text fields = inline HTML
All text fields except code lines and URLs are inserted as HTML (escape `& < >` yourself, e.g. `&lt;model&gt;`).
Shorthands: `==text==` → `<em class="hl">text</em>` (orange highlight), `` `x` `` → `<code class="ic">x</code>`.
Useful inline classes from the theme: `<b>`, `<span class="mono">`, `<span class="chip">` / `chip blue|green|grey`, `<span class="cmd">` (tables).

## Code lines (layout `code`)
Plain text, auto-escaped and auto-highlighted: leading `$ ` → prompt (green); ` -x` / ` --flag` → blue; `'…'`/`"…"` → yellow; `<…>` → yellow placeholder; `# …` → dim comment.
A line can be an object: `{"text": "...", "hl": true}` (orange highlight band after typing), `{"text": "...", "out": true}` (grey output line, no highlighting),
`{"text": "...", "html": "<raw>"}` (raw HTML; `text` still sets typing length).
Typing timing (recovered exactly): steps = len(text); duration = min(600, 100 + 12·steps) ms; next line starts +60 ms after; next terminal starts 140 ms before the previous one finishes; note appears 300 ms after its terminal; highlight band 210 ms after the line finishes.

## Fonts
build.py collects all rendered text (slides, notes, UI, meta.title) + ` ?—…≤✓`. If the bundled 2-01 subsets in `assets/fonts/` cover every char, they are embedded verbatim (→ byte-identical rebuild); otherwise all four fonts are re-subset (fontTools, `layout_features=*`, WOFF2) from a source font. Search order for each slot: the matching `DG_FONT_*` environment variable, `assets/fonts/sources/` (not committed), `~/.local/share/fonts/` and `~/Library/Fonts/`, then common system paths such as `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` (face "Noto Sans CJK SC"). Variable Outfit and JetBrains Mono filenames are listed in `references/fonts.md`. `--resubset` forces it.
If a source font is missing, chars fall back to the CSS stack (PingFang SC / Microsoft YaHei / system) and a warning is printed.

## Images
`image-text.image`, `people[].photo`: path relative to the spec file, or relative to `assets/` (e.g. `brand/d-robotics-logo-full.png`); embedded as base64 data URIs.

## Layout `diagram` (NEW — dg-deck extension, not in the original)
Animated SVG explainer. Field reference: references/layouts.md → "diagram". The un-animated DOM is the final frame, so static/print/reduced-motion/export all show it. The timeline JSON is embedded per slide (`script.dgm-tl`). `assets/templates/diagram.css` and `assets/templates/diagram.js` are included only when a diagram slide exists.

## Viewer UI language
The page hint (翻页 / turn pages), the prev/next button labels and the empty-notes text follow `meta.lang`: `en`, `en-US`, … → English; anything else → Chinese (the original strings, so zh decks are unchanged). Override single strings with `meta.ui` (`hint`, `prev`, `next`, `no_notes`).

## Layout `series-cover` (NEW — series cover, slide 1)
Fields: `chapter`, `chapter_name`, `lesson`, `title` (required); `highlight`, `subtitle`, `visual`, `theme`, `badge`, `series`, `mock`, `nav` (optional). The cover text is `title`; the nav/footer label is `nav` (default 封面 / Cover). Language follows `meta.lang`. Missing required fields stop the build. Reference: references/layouts.md → "series-cover". The platform thumbnail is rendered from the same slide by `scripts/render_cover.py --spec <deck.json>`.
