# Contributing

## 中文

欢迎贡献新的 Skill、模板或文档。每个公开 Skill 至少包含 `SKILL.md`，并使用 kebab-case 目录名。可选目录包括 `references/`、`scripts/`、`assets/` 和 `agents/`。

提交前请确认：所有引用的本地文件存在；文档链接可访问；脚本在其目标环境可运行；不包含凭据、私有数据、模型权重、大型数据集或机器专属路径。运行 `git diff --check` 与 `git status --short` 检查待提交内容。

`SKILL.md` 应优先描述 Codex 与 Claude Code 都能理解的通用工作流。只在确有需要时添加 `agents/openai.yaml` 或 Claude Code 插件元数据。

## English

Contributions of Skills, templates, and documentation are welcome. Every public Skill must contain `SKILL.md` and use a kebab-case directory name. Optional directories include `references/`, `scripts/`, `assets/`, and `agents/`.

Before committing, verify that referenced local files exist, documentation links work, scripts run in their target environment, and no credentials, private data, model weights, large datasets, or machine-specific paths are included. Run `git diff --check` and `git status --short` to inspect the change.

Keep `SKILL.md` focused on workflows understood by both Codex and Claude Code. Add `agents/openai.yaml` or Claude Code plugin metadata only when needed.
