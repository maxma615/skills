---
name: rdk-course-slides-generator
description: Use when converting an RDK course handbook Markdown file into a self-contained Chinese or English HTML lesson deck, translating a generated Chinese blueprint to English, or validating an RDK course deck.
---

# RDK Course Slides Generator

将 RDK 小课堂讲义转换为可离线打开、键盘翻页的单文件 HTML 课件。Use this only for RDK course material, not for generic slide decks, PPT conversion, video rendering, or writing a handbook from scratch.

## Route the request

| Goal | Read before acting |
| --- | --- |
| New deck from a handbook | [handbook-parser.md](references/workflows/handbook-parser.md), then [html-slide-composer.md](references/workflows/html-slide-composer.md) |
| Chinese and English versions | The two workflow references above, then [bilingual-variant.md](references/workflows/bilingual-variant.md) |
| Review an existing deck | [visual-review.md](references/workflows/visual-review.md) |

Before generation, obtain the handbook path, target language(s), and output path. If the output already exists, show the path and get approval before replacing it; the renderer does not create backups automatically.

## Operating constraints

- Derive slide content only from the supplied handbook. Preserve commands, versions, URLs, and product names; do not invent course material.
- Use the bundled renderer only with trusted blueprint JSON. It emits values directly into HTML.
- For structure, terminology, icons, or visual rules, read the matching reference: [schema](references/handbook-schema.md), [glossary](references/i18n-glossary.md), [icons](references/icon-vocabulary.md), [patterns](references/slide-patterns.md), and [design system](references/design-system.md).
- Chinese and English variants must retain the same slide count, order, patterns, icons, and tint assignments.
- The bundled D-Robotics branding assets are for authorized RDK course material only. Confirm branding and distribution rights before publishing generated decks.

## Render and validate

Use the renderer from this installed Skill directory:

```sh
python scripts/build-html.py --blueprint path/to/blueprint.json --output path/to/course.html
```

Use `--lang cn` or `--lang en` to override the blueprint language, and `--assets-dir` only when approved replacement logos are supplied. For the bundled regression fixture, run:

```sh
python scripts/validate_build_html.py
```

After static checks pass, open the generated HTML locally and verify navigation, title overflow, color cards, logo embedding, and reduced-motion behavior. Report any visual issue rather than silently altering course content.
