---
name: dg-deck-courseware
description: >-
  Use when making or revising a D-Robotics / RDK-style single-file HTML
  courseware or presentation deck (课件), including animated explainer diagrams,
  from a JSON spec, lesson notes, or an RDK course blueprint JSON.
---

# dg-deck 课件生成

Generate a D-Robotics / RDK-style single-file offline HTML courseware deck (课件). Output is one offline HTML file with fonts, logos, icons, and photos inlined as base64.

This skill renders the deck. `scripts/convert_rdk_blueprint.py` turns an RDK course blueprint JSON (cover, cards, checklist, timeline, flow, code, resources, closing) into a dg-deck spec. Docs: [usage](references/usage.md), [spec](references/spec.md), and [layouts](references/layouts.md). The layouts doc has a diagram section.

Run every script from this Skill directory with a virtualenv that has `requirements.txt` installed. `fonttools` and `brotli` are required to build. `playwright` and `Pillow` are required to render, preview, and smoke-test. `beautifulsoup4` is required only by `extract_spec.py`. `rembg` is optional and is only for cutting out board photos.

## Setup

From this Skill directory:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

On Windows, use `.venv\Scripts\python` instead of `.venv/bin/python`. To skip the Playwright browser download, install the Python package only and pass a local Chrome or Chromium with `--chrome /path/to/chrome`, or set `CHROME`. `render.py`, `preview.py`, and `smoke_test.py` try `--chrome`, then `$CHROME`, then a system Chrome/Chromium, then Playwright's Chromium.

## Steps

1. **Get the content into a dg-deck JSON spec.**
   - **From scratch or from lesson notes:** write the spec by hand following [references/spec.md](references/spec.md). Pick layouts from [references/layouts.md](references/layouts.md) and respect their capacity notes.
     - `examples/lesson-2-01.zh.json` reproduces the original 24-slide v3 deck exactly. It deliberately keeps the old X5U-only wording, so don't copy facts from it; use the board facts below.
     - `examples/layout-gallery.zh.json` shows every layout.
     - For a large deck, generate the spec from a small Python script, e.g. `make_spec.py` next to the deck, so revisions are reproducible.
   - **From an RDK course blueprint JSON:** run `python scripts/convert_rdk_blueprint.py blueprint.json -o spec.json`, then review it. The blueprint is a JSON object with `meta` and `slides`, where each slide has a `pattern` such as `cover`, `cards-3`, `split-checklist`, `flow-5`, `code-highlight`, `resource-list`, or `closing`. For an RDK 小课堂 lesson add `--chapter N --chapter-name <章名> --lesson M` (optionally `--cover-title`, `--highlight`, `--subtitle`, `--visual`) so slide 1 becomes the series cover. Blueprints carry no speaker notes, and an empty checklist renders as a heading only.
   - **To edit an existing dg-deck HTML whose spec is lost:** run `python scripts/extract_spec.py deck.html -o spec.json`.
   - **Slide 1 of every RDK 小课堂 deck (zh and en) is the `series-cover` layout.** Fill `chapter`, `chapter_name`, `lesson`, `title` and `highlight` (plus optional `subtitle` and `visual`: `bpu`, `quant` or `none`); the badge `N-MM` and the full title 【RDK 小课堂】第 N 章 <章名> · 第 M 课｜<课名> (en: [RDK Classroom] Chapter N <name> · Lesson M | <title>) are derived from those fields. Don't hand-edit the cover afterwards. See the `series-cover` section of [references/layouts.md](references/layouts.md).
   - **Viewer UI language follows `meta.lang`.** The page-turn hint, prev/next labels and the empty-notes text are Chinese for `zh` and English for `en`; override single strings with `meta.ui`.
2. **Add animated diagrams where a concept is about relationships, flow, scale or change.** Use the `diagram` layout; its field reference is in [references/layouts.md](references/layouts.md). Good targets:
   - CPU/BPU division of labour
   - a pipeline (preprocess, BPU, postprocess)
   - a heterogeneous model split between BPU and CPU
   - board line-ups
   - which model fits which board
   - quantization or calibration
   - the development flow
   - operator placement and fallback
   - measured multi-thread latency and FPS
3. **Build:** run `python scripts/build.py spec.json -o build/out.html`. It re-subsets the fonts automatically when new characters appear; `--resubset` forces it. Write output under `build/` or another directory outside `examples/`. The `build/` directory is gitignored.
4. **Render and check.**
   - Run `python scripts/render.py build/out.html -o build/png --pdf build/out.pdf`. It writes per-slide PNGs, contact_sheet.png and an overflow report.
   - Look at the contact sheet and fix any overflow. In hand-written specs keep code lines to about 58 monospace characters; break long filenames after underscores.
   - Run `python scripts/smoke_test.py build/out.html`.
   - **Platform thumbnail:** render it from the same template and the same fields as slide 1, e.g. `python scripts/render_cover.py --spec spec.json -o build/cover --thumbs`. It writes the 16:9 cover, a 4:3 crop and small thumbnails, and exits non-zero on overflow. Never design the thumbnail separately.
5. **Preview the animations.** Run `python scripts/preview.py build/out.html -o build/preview/`; `--slides 9,22` limits it to those slides. It records an MP4 for each diagram slide plus a `*.frames.jpg` with one frame per second. `ffmpeg` must be on `PATH`.
   - Look at the frame sheets yourself before delivering.
   - Check for leftover white boxes, labels covered by moving tokens, invisible arrowheads, and blank captions.
6. **Version and deliver.**
   - Put each revision in a new `vN/` folder and leave earlier versions untouched.
   - Deliver the HTML, plus preview MP4s for the slides that changed.
   - When the user keeps course files on their own computer, also copy them into that lesson's chapter folder there, never loose in their home directory.
   - Viewer keys: ←/→ to change page, N for notes, F for fullscreen, S for the scroll view, R to replay an animation.
   - URL params: `?mode=scroll`, `?print=1`, `?static=1`, `?export=1`.

## Visual style: Google for Developers explainer look

Style notes are in [references/style-notes.md](references/style-notes.md). The frame-sheet images named there are not bundled; the written observations are the style reference.

**Shapes and colour**

- Use flat, thin-outline rounded boxes, small sans-serif labels and lots of white space.
- CPU is always Google blue. BPU is always brand orange #FF5A00/#FF3C00. Neutral elements are grey #DADCE0.
- Call a part out by recolouring its outline or fill and dimming the rest (`focus`, `state`/`on`), not by adding decoration.

**Motion**

- Build up one idea at a time with `show`, one new element per step.
- Camera push-in and pull-out: about 1.1 s with cubic-bezier(.2,0,0,1), no bounce.
- Use translucent `band`s to mark a region and MAC grids to show scale.
- Tokens move along lanes below or beside the boxes so they never cover a label.
- Each step gets one bottom caption sentence.

**Final frame**

- The un-animated DOM is the final frame, with every element visible and nothing dimmed. That frame is what `?static=1`, `?print=1`, reduced-motion and PNG/PDF export show.

**Everything blends into the slide background.**

- Draw diagrams and info panels directly on the page: no white card, panel, border or shadow around a diagram or any sub-panel (e.g. a precision-cost note), with only a soft edge fade.
- Grouping inside a diagram uses a faint dashed outline, not a filled white box.
- Coloured CPU/BPU regions that are part of the drawing are fine.

**Text conventions**

- Don't write “Animated” or 「动画」 in eyebrows, footers or titles.
- Give every diagram SVG unique marker ids so arrowheads render when several diagrams share a deck. `assets/templates/diagram.js` already does this; keep it that way if you edit it.
- Real photos, such as board photos, go in with the `photo` element. Cut the background out with rembg (optional `pip install rembg`; keep `cutout.py` in that deck's `assets/boards/`, not in this Skill) and record each photo's source in that deck's `assets/SOURCES.md`.

## Content rules

- **Brand:** the D-Robotics icon goes top-left on every slide. The orange is #FF5A00/#FF3C00 and the accent is Google blue. The white logo variant (`assets/brand/d-robotics-icon-dark.png`) is self-made, not official; confirm with design before any external use.
- **Layouts:**
  - Faithful to the original: cover, cards, section, bullets, code, flow, table, bars, links, closing.
  - Rebuilt, not original: agenda, compare, metrics, image-text, timeline, people, quote, podium.
  - New: diagram, series-cover.
  - Say so if asked.
- **Never invent numbers.**
  - Every figure on a slide must come from docs, the Model Zoo repo, or a real board test.
  - Label each figure with its source, e.g. README reference vs 实测 plus the board. Put no test dates on slides.
  - Label illustrative visuals 「示意」.
  - When a claim from notes or a handoff is unverified, verify it (RDK docs connector, repo configs, or an on-board test) or drop it.
- **S600 multi-core / multi-thread performance.** When a slide shows this, present only the measured latency and FPS for each thread count, for example 1, 4, and 12 threads.
  - Leave the test date off the slide.
  - Leave off any explanation that `core_num` decides how many cores one inference uses. A single-core-compiled model still runs across multiple cores when several threads submit work, so that framing is unconvincing.
  - Treat S600 as a special case. Do not present this as a general rule for other boards.

### Board facts

- **X5:** Bayes-e, 10 TOPS, `.bin` models, one packed NV12 input. Its SoC name can read X5U, X5H or X5M, so never write only X5U.
- **S100 / S100P / S600:** Nash-e / Nash-m / Nash-p, 80 / 128 / up to 560 TOPS, `.hbm` models. NV12 input is split into Y and UV. S100 and S100P look identical, so one photo may serve both.
- **S600:** has 4 BPU cores (bpu0–bpu3). `/sys/devices/system/bpu/core_num` reports the board's hardware core count, not the model's.
- **Toolchain versions:** write 「以工具链文档为准」.

### Multi-core facts

Background knowledge for checking a claim. Keep it off the slide. These measurements are an S600 special case, not a general rule.

Verified on S600 with hrt_model_exec 3.13.6.

- **Cores per inference:** how many BPU cores one inference uses is fixed at conversion time by `compiler_parameters.core_num` in the YAML. `hrt_model_exec model_info` shows it as `"CORE_NUM"` in the model description. Model Zoo ResNet-18 is `core_num: 1`.
- **`--thread_num`:** only the number of concurrent submission threads for a test (X5 1–8, S series 1–32). It never sets the core count.
  - With a single-core model, extra threads let the runtime spread tasks across cores. This raises throughput, and the load is uneven.
- **`--core_id`:** 1-based, where 0 means any core and 1 means bpu0.
  - A model with core_num>1 must be given exactly that many cores in `--core_id`, or it errors.
- **More cores is not automatically faster.**

### Boundaries

- Don't modify the source repos.
- Keep generated decks outside this Skill's `examples/` directory unless you are adding a reference example.
- On RDK boards, write only under `/tmp/<lesson>`. Don't install packages, change config or reboot.
