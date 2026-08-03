# Public Skills Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the current workspace as public `maxma615/skills` without exposing its existing concrete skills or project material.

**Architecture:** Keep the existing layout, but publish repository documentation, directory markers, and the generic new-skill template through strict `.gitignore` rules. Future packages use shared `SKILL.md` instructions, with optional Codex and Claude Code adapters.

**Tech Stack:** Git, GitHub CLI, Markdown, `.gitignore`.

## Global Constraints

- GitHub repository: `maxma615/skills`, visibility `public`, default branch `main`.
- Root documentation is Chinese and English; design and plan records remain Chinese.
- Do not publish either existing skill package or its project note in the first release.
- Use `SKILL.md` as the shared future entry point; `agents/openai.yaml` and `.claude-plugin/` are optional adapters.
- License: MIT.

---

### Task 1: Protect local skill and project material

**Files:**

- Modify: `.gitignore`
- Create: `skills/.gitkeep`
- Create: `projects/.gitkeep`
- Create: `shared/.gitkeep`

**Interfaces:**

- Consumes: Untracked contents in `skills/`, `projects/`, and `shared/`.
- Produces: A public-safe staging boundary that retains the three directories without adding their current contents.

- [ ] **Step 1: Add explicit first-release ignore rules**

Append this exact block after `archive/` in `.gitignore`:

```gitignore
# First public release: keep local work material out of the repository.
/skills/*
!/skills/.gitkeep
/projects/*
!/projects/.gitkeep
/shared/*
!/shared/.gitkeep
```

- [ ] **Step 2: Create the directory markers**

Run `New-Item -ItemType File -Force skills/.gitkeep, projects/.gitkeep, shared/.gitkeep`.

Expected: each directory has a trackable marker while its existing material remains ignored.

- [ ] **Step 3: Verify the ignore boundary**

Run `git check-ignore -v skills/rdk-yolo-toolkit/SKILL.md projects/rdk-yolo-toolkit.md shared/README.md archive/` and `git status --short --ignored`.

Expected: all four material paths are ignored; only the three `.gitkeep` markers are eligible to stage.

- [ ] **Step 4: Commit the protection rules**

Run `git add .gitignore skills/.gitkeep projects/.gitkeep shared/.gitkeep` followed by `git commit -m "chore: protect local skill materials"`.

### Task 2: Create cross-agent public documentation

**Files:**

- Modify: `README.md`
- Modify: `AGENTS.md`
- Create: `CONTRIBUTING.md`
- Create: `CLAUDE.md`
- Create: `LICENSE`

**Interfaces:**

- Consumes: `docs/superpowers/specs/2026-08-03-personal-skills-repository-design.md`.
- Produces: A bilingual landing page and contributor instructions for people, Codex, and Claude Code.

- [ ] **Step 1: Replace the root README with bilingual public guidance**

Include Chinese and English sections for repository purpose, all five top-level directories, the future `SKILL.md` contract, optional `agents/openai.yaml` and `.claude-plugin/` adapters, and the fact that no skills are published yet.

- [ ] **Step 2: Add contributor and agent guidance**

Create `CONTRIBUTING.md` with the package layout, credential and large-artifact prohibition, and validation commands. Create `CLAUDE.md` with the same boundaries and an instruction to read `AGENTS.md`; update `AGENTS.md` to remove its obsolete claim that this workspace has no Git history.

- [ ] **Step 3: Add the MIT License**

Create the standard MIT License with copyright holder `Max.Ma` and year `2026`.

 - [ ] **Step 4: Publish the generic new-skill template**

Review `templates/skill-project/PROJECT.md` and `templates/skill-project/README.md` for credentials, local paths, and references to existing skills. If clean, stage both files as the public starting point for future skill projects.

 - [ ] **Step 5: Validate public documentation and template**

Run `rg -n "TODO|TBD|Machao615|20_Dev_Projects|C:\\Users" README.md CONTRIBUTING.md CLAUDE.md AGENTS.md LICENSE` and `git diff --check`.

Expected: no first-command matches and no whitespace errors.

 - [ ] **Step 6: Commit the documentation and template**

Run `git add README.md AGENTS.md CONTRIBUTING.md CLAUDE.md LICENSE templates/skill-project` followed by `git commit -m "docs: add public skills repository guidance"`.

### Task 3: Publish and verify the public repository

**Files:**

- Modify: none
- Test: Git index and GitHub remote repository

**Interfaces:**

- Consumes: Clean local commits on `main` and authenticated GitHub account `maxma615`.
- Produces: Public remote `origin` pointing to `https://github.com/maxma615/skills.git`.

- [ ] **Step 1: Audit the exact initial public tree**

Run `git ls-files`, `git status --short --branch`, and `git log --oneline --decorate`.

Expected: the index contains only repository guidance, directory markers, and approved design and plan documents; it contains no `skills/rdk-*`, `projects/rdk-*`, or existing `shared/` material.

- [ ] **Step 2: Create and push the GitHub repository**

Run `gh repo create maxma615/skills --public --source . --remote origin --push`.

Expected: GitHub creates the repository, adds `origin`, and pushes `main`.

- [ ] **Step 3: Verify remote settings and contents**

Run `gh repo view maxma615/skills --json nameWithOwner,visibility,defaultBranchRef,url`, `git remote -v`, and `git status --short --branch`.

Expected: `visibility` is `PUBLIC`, default branch is `main`, the URL is `https://github.com/maxma615/skills`, and the local branch tracks `origin/main` with a clean worktree.

- [ ] **Step 4: Commit the implementation-plan record if needed**

Run `git add docs/superpowers/plans/2026-08-03-public-skills-repository.md`, then `git commit -m "docs: add public repository implementation plan"`, then `git push`. If the plan was already committed, skip that commit and run only `git push`.
