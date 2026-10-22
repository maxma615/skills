# Fonts

The files in `assets/fonts/` are WOFF2 subsets, small enough to commit. They are embedded verbatim when they already cover every character in the deck. `build.py` re-subsets only when new characters appear, or when `--resubset` is passed.

CSS family names in the deck are `DG CJK`, `DG Sans`, and `DG Mono` (`assets/templates/fonts.css.tmpl`). Name-table metadata inside the subset files still identifies the upstream families so the license can be read from the font. License text: `assets/fonts/OFL.txt`.

| Bundled file | Upstream | Version | What the subset covers |
| --- | --- | --- | --- |
| `dg-cjk-400.woff2` | Noto Sans CJK SC Regular | 2.004 | 589 code points from the original 2-01 deck |
| `dg-cjk-700.woff2` | Noto Sans CJK SC Bold | 2.004 | same 589 code points |
| `dg-sans-outfit-var.woff2` | Outfit variable | 1.100 | 95 code points |
| `dg-mono-jetbrains-var.woff2` | JetBrains Mono variable | 2.211 | 97 code points |

All four are under the SIL Open Font License 1.1, which allows bundling and redistributing subsets with the copyright notice and license. Do not sell the font files by themselves. Source Han Sans, the upstream of Noto Sans CJK, reserves the font name `Source`.

## Obtaining source fonts for a re-subset

Full source fonts are not in this package. Put them in `assets/fonts/sources/` (gitignored), in `~/.local/share/fonts/` or `~/Library/Fonts/`, or point these variables at the files:

| Variable | Preferred file | Where to get it |
| --- | --- | --- |
| `DG_FONT_CJK_REGULAR` | `NotoSansCJK-Regular.ttc` (face `Noto Sans CJK SC`) | `apt install fonts-noto-cjk`, or [Noto CJK](https://github.com/notofonts/noto-cjk) |
| `DG_FONT_CJK_BOLD` | `NotoSansCJK-Bold.ttc` (same face) | same package |
| `DG_FONT_SANS` | `Outfit-VariableFont_wght.ttf` | [Outfit](https://github.com/Outfitio/Outfit-Fonts) (OFL) |
| `DG_FONT_MONO` | `JetBrainsMono[wght].ttf` or `JetBrainsMono-VariableFont_wght.ttf` | [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) (OFL). A static `JetBrainsMono-Regular.ttf` works, but it has no weight axis. |

`build.py` also checks the usual Debian/Ubuntu paths, including `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` and `/usr/share/fonts/truetype/jetbrains-mono/`. If a source font is missing, characters that are not in the bundled subset fall back to the CSS stack (PingFang SC / Microsoft YaHei / the system font) and the build prints a warning.
