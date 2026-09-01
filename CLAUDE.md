# Claude Code Guidance

Read `AGENTS.md` before making changes. This repository maintains reusable Skills for both Codex and Claude Code.

- Keep installable packages in `skills/` and their development material in `projects/`.
- Put reusable material in `shared/` and starter material in `templates/`.
- Keep third-party Skill origins in `sources/`; do not mirror their contents unless explicit permission and license review allow it.
- Use `scripts/install-personal-skills.ps1` on Windows or `scripts/install-personal-skills.sh` on WSL to install the four Skills maintained here.
- Keep historical, large, or machine-specific material in `archive/`; do not commit it.
- Every published Skill requires `SKILL.md`; keep it portable across agents.
- Do not add `.claude-plugin/` metadata until there is at least one Skill to distribute as a Claude Code plugin.
- Do not commit credentials, private data, model weights, generated binaries, or large datasets.
