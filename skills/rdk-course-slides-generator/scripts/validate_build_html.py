#!/usr/bin/env python3
"""Validate the bundled renderer against the Chinese and English fixtures.

This check forces ASCII stdout so a regression such as a non-ASCII status
character breaking a Windows GBK console is caught before publishing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from shutil import which
import subprocess
import sys
import tempfile


SKILL_ROOT = Path(__file__).resolve().parents[1]
RENDERER = SKILL_ROOT / "scripts" / "build-html.py"
SAMPLES = {
    "cn": SKILL_ROOT / "examples" / "lesson-01-blueprint-cn.json",
    "en": SKILL_ROOT / "examples" / "lesson-01-blueprint-en.json",
}


def slide_shape(slide: dict) -> tuple:
    return (
        slide.get("pattern"),
        slide.get("icon"),
        slide.get("tint"),
        tuple(
            (card.get("icon"), card.get("tint"))
            for card in slide.get("cards", [])
        ),
        tuple(len(slide.get(key, [])) for key in ("cards", "steps", "items", "resources")),
    )


def validate_initial_navigation(html: str) -> None:
    """Exercise the generated initial page/progress state when Node is available."""
    node = which("node")
    if node is None:
        if "let index = -1;" not in html:
            raise AssertionError("Generated navigation does not initialize before show(0).")
        return

    runner = r'''
const fs = require("fs");
const html = fs.readFileSync(0, "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (!match) throw new Error("Missing runtime script");
const makeSlide = (active = false) => ({ classList: {
  items: new Set(active ? ["active"] : []),
  contains(name) { return this.items.has(name); },
  remove(name) { this.items.delete(name); },
  add(name) { this.items.add(name); },
  toggle(name, force) {
    if (force === undefined) this.items.has(name) ? this.items.delete(name) : this.items.add(name);
    else if (force) this.items.add(name); else this.items.delete(name);
  },
}});
const slides = [makeSlide(true), makeSlide(false)];
const page = { textContent: "" };
const progress = { style: { width: "" } };
const controls = { prev: {}, next: {} };
global.document = {
  querySelectorAll: () => slides,
  getElementById: (id) => ({ page, progress, ...controls })[id],
};
global.window = { addEventListener() {} };
eval(match[1]);
if (page.textContent !== "1 / 2" || progress.style.width !== "50%") {
  throw new Error(`Initial navigation not initialized: page=${page.textContent}; width=${progress.style.width}`);
}
'''
    result = subprocess.run(
        [node, "-e", runner],
        input=html.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise AssertionError(message or "Initial navigation validation failed.")


def main() -> None:
    if not RENDERER.is_file():
        raise AssertionError(f"Missing renderer: {RENDERER}")
    missing = [path for path in SAMPLES.values() if not path.is_file()]
    if missing:
        raise AssertionError("Missing sample blueprint: " + ", ".join(map(str, missing)))

    blueprints = {lang: json.loads(path.read_text(encoding="utf-8")) for lang, path in SAMPLES.items()}
    if len(blueprints["cn"]["slides"]) != len(blueprints["en"]["slides"]):
        raise AssertionError("Bilingual fixtures have different slide counts.")
    if [slide_shape(slide) for slide in blueprints["cn"]["slides"]] != [
        slide_shape(slide) for slide in blueprints["en"]["slides"]
    ]:
        raise AssertionError("Bilingual fixtures have different slide structures.")
    for language, blueprint in blueprints.items():
        incomplete_resources = [
            resource.get("name", "unnamed resource")
            for slide in blueprint["slides"]
            for resource in slide.get("resources", [])
            if resource.get("href") in {"", "#"}
            or "TBD" in resource.get("desc", "")
            or "待补充" in resource.get("desc", "")
        ]
        if incomplete_resources:
            raise AssertionError(
                f"{language} fixture contains incomplete resources: "
                + ", ".join(incomplete_resources)
            )

    with tempfile.TemporaryDirectory(prefix="rdk-course-skill-") as temp_dir:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "ascii"
        for language, blueprint in SAMPLES.items():
            output = Path(temp_dir) / f"lesson-01-{language}.html"
            result = subprocess.run(
                [sys.executable, str(RENDERER), "--blueprint", str(blueprint), "--output", str(output)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            if result.returncode != 0:
                raise AssertionError(
                    f"Renderer failed for {language} under ASCII stdout:\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

            html = output.read_text(encoding="utf-8")
            checks = {
                "HTML closes": "</html>" in html,
                "slide count matches": html.count("data-title=") == len(blueprints[language]["slides"]),
                "one embedded logo": html.count("data:image/png;base64") == 1,
                "no external asset path": "assets/" not in html,
                "reasonable output size": 20 * 1024 < output.stat().st_size < 100 * 1024,
            }
            failures = [name for name, passed in checks.items() if not passed]
            if failures:
                raise AssertionError(f"{language} validation failed: " + ", ".join(failures))
            if language == "cn":
                validate_initial_navigation(html)

    print("Renderer validation passed.")


if __name__ == "__main__":
    main()
