# Repository Guidelines

## Project Structure & Module Organization

This repository is a workspace for personal Codex Skills. Keep installable skill packages separate from planning notes and raw work artifacts.

- `skills/`: publishable skill packages. Each skill should include `SKILL.md`; optional subdirectories include `references/`, `scripts/`, `assets/`, and `agents/`.
- `projects/`: project briefs, design notes, task lists, and validation plans for skills under development.
- `shared/`: reusable references, scripts, and assets used by multiple skills.
- `templates/`: starter templates, especially `templates/skill-project` for new skill planning.
- `sources/`: official origins and installation notes for third-party Skills; do not mirror their content without explicit permission.
- `scripts/`: cross-platform helpers for installing this repository's personal Skills.
- `archive/`: historical workspaces, old distributions, large source materials, or experimental artifacts. Do not treat archived projects as active source unless explicitly requested.

## Build, Test, and Development Commands

There is no root build system. Work at the smallest relevant scope.

- `Get-ChildItem skills`: list current skill packages on Windows PowerShell.
- `cp -r templates/skill-project projects/<skill-name>`: start a new skill project scaffold in POSIX shells.
- `rg "pattern" skills shared projects`: search workspace content quickly.
- `bash skills/<skill-name>/scripts/<script>.sh` or `node skills/<skill-name>/scripts/<script>.mjs`: run skill-specific helpers when provided.

## Coding Style & Naming Conventions

Use kebab-case for skill and project directory names, for example `skills/rdk-yolo-toolkit`. Keep every skill’s main instructions in `SKILL.md` with valid front matter containing at least `name` and `description`. Prefer Markdown headings, concise procedural steps, and relative references to local files. Put reusable long-form details in `references/` rather than overloading `SKILL.md`.

## Testing Guidelines

No global test framework is configured. Validate changes with the relevant skill’s own scripts, examples, or documented manual checks. For skill edits, verify that referenced files exist, scripts are executable in their intended environment, and instructions can be followed from a clean checkout. Name ad hoc validation scripts descriptively, such as `validate-skills.mjs` or `check_rdkx5_env.sh`.

## Commit & Pull Request Guidelines

Use clear, conventional commit messages, such as `add rdk yolo references` or `update quantization troubleshooting`. Pull requests should summarize the changed skill or project, list validation performed, link related notes in `projects/`, and include screenshots only when visual assets or UI behavior changed.

## Security & Configuration Tips

Do not commit credentials, private model weights, large datasets, generated binaries, or machine-specific paths. Keep bulky or temporary materials in `archive/` or external workspaces, not in publishable `skills/` packages.
