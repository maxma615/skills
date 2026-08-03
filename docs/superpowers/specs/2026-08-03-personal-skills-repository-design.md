# Personal Skills Repository Design

## Goal

Publish a public GitHub repository at `maxma615/skills` that is ready to host
personal Codex Skills without publishing any skill implementation in the first
release.

## Repository model

The repository uses `main` as its default branch and the MIT License. Its root
keeps these clearly separated areas:

- `skills/`: installable skill packages; initially empty.
- `projects/`: planning material for skills being developed.
- `shared/`: reusable references, scripts, and assets.
- `templates/`: starter material for new skill projects.
- `archive/`: local historical or bulky material; excluded from Git.

Future published skills may be grouped by topic. Each package must contain a
`SKILL.md` file and may contain `agents/openai.yaml`, `references/`, `scripts/`,
and `assets/`. Topic README files act as category entry points once a category
contains published skills.

## Public-facing documentation

The root README is bilingual (Chinese and English) and describes the repository
purpose, directory responsibilities, the skill package contract, and local
validation expectations. `CONTRIBUTING.md` explains how to propose a skill or
documentation change. `.gitignore` prevents local editor files, credentials,
large generated artifacts, and the repository's `archive/` workspace from
being committed.

## Initial scope

The initial public repository contains only the structure, guidance, license,
and Git metadata. It deliberately excludes concrete skills, release automation,
package-manager configuration, Changesets, and CI workflows. Those will be
added only when an actual skill requires them.

## Validation

Before publishing, verify that required directories and documents exist, all
README links resolve, ignored material is not staged, and the first public
commit is clean. Confirm the GitHub repository is public and that its default
branch is `main`.
