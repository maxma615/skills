# assets

Paths are relative to this Skill. Brand files are not covered by the repository MIT license. See the repository `NOTICE.md`.

## fonts/

WOFF2 subsets extracted from the original lesson HTML. License: SIL OFL 1.1 (`assets/fonts/OFL.txt`). Details and how to obtain full source fonts: [fonts.md](fonts.md).

## brand/

- `d-robotics-icon.png` (310×265): the icon at the top-left of every light slide.
- `d-robotics-icon-dark.png`: the same icon drawn in white for `.slide.dark`. This white variant is self-made, not an official D-Robotics logo. Confirm it with design before any external use.
- `d-robotics-logo-full.png` (800×193): the closing-slide 「地瓜机器人」 logo.
- `d-robotics-logo-full-en.png`: the English closing-slide logo. It was not in the original lesson HTML.
- `d-robotics-logo-full-dark.png`, `d-robotics-logo-full-white.png`, `d-robotics-logo-full-en-dark.png`, `d-robotics-logo-full-en-white.png`: wordmark variants for the `series-cover` `dark` theme (`…-dark.png`) and `orange` theme (`…-white.png`) (the default `light` theme uses the two original files). These variants are self-made, not official D-Robotics files. Confirm them with design before any external use.
- `d-robotics-logo-official.png`: a reference copy of the horizontal D-Robotics logo. `build.py` does not embed it.

## icons/

24×24 stroke icons. Color follows the text. They are based on Lucide (ISC); see `NOTICE.md`.

- From the original lesson, plus the eyebrow sparkle: terminal, network, film, layers, list-checks, search, zap, target, flask, graduation-cap, grid, code, book-open, wrench, rocket, eye, sparkle.
- Extra icons used by RDK course blueprints: chip, robot, message, arm, star, puzzle, globe, github, video.
- Aliases in `scripts/build.py`: brain → network, list-check → list-checks, gradcap → graduation-cap.

The original 2-01 lesson has no content photographs. Diagrams are CSS/SVG. The only embedded bitmaps are the brand marks above. Board photos belong to the deck being built, not to this Skill.
