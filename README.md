# Max.Ma Skills

[English](#english) | [中文](#中文)

## 中文

这是 Max.Ma 维护的跨代理 Skills 仓库，面向 Codex 与 Claude Code。它用于沉淀可复用的工作流、领域知识和工具约定。

### 目录

- `skills/`：可安装的 Skill 包。首版尚未发布具体 Skill。
- `projects/`：Skill 开发过程中的项目说明、设计和验证材料。
- `shared/`：多个 Skill 可复用的参考资料、脚本和资产。
- `templates/`：新建 Skill 项目的起始模板。
- `archive/`：本地历史材料和大型临时文件，不纳入版本控制。

### Skill 包约定

每个公开 Skill 以 `SKILL.md` 为必需入口，可按需包含 `references/`、`scripts/`、`assets/`。`agents/openai.yaml` 可提供 Codex 专属界面元数据；需要作为 Claude Code 插件分发时，再添加 `.claude-plugin/` 元数据。

贡献和本地验证方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## English

This is Max.Ma's cross-agent Skills repository for Codex and Claude Code. It collects reusable workflows, domain knowledge, and tool conventions.

### Layout

- `skills/`: Installable Skill packages. No concrete Skills are published in the first release.
- `projects/`: Project briefs, designs, and validation material for Skills in development.
- `shared/`: References, scripts, and assets shared by multiple Skills.
- `templates/`: Starter material for new Skill projects.
- `archive/`: Local historical material and large temporary files; excluded from version control.

### Skill package contract

Every published Skill has a required `SKILL.md` entry point and may include `references/`, `scripts/`, and `assets/`. `agents/openai.yaml` may provide Codex-specific UI metadata. Add `.claude-plugin/` metadata only when distributing Skills as a Claude Code plugin.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and local validation guidance.
