# 个人 Skills 仓库设计

## 目标

创建公开 GitHub 仓库 `maxma615/skills`，作为个人 Codex 与 Claude Code Skills 的
长期发布与维护入口。首个版本只发布仓库结构与协作约定，不发布任何具体 Skill 实现。

## 仓库模型

仓库默认分支为 `main`，采用 MIT License。根目录保留以下职责清晰的区域：

- `skills/`：可安装的 Skill 包；首版为空。
- `projects/`：开发中 Skill 的项目说明、设计记录和任务材料。
- `shared/`：多个 Skill 可复用的参考资料、脚本和资产。
- `templates/`：新建 Skill 项目的起始模板。
- `archive/`：本地历史材料或大文件；不纳入 Git。

后续发布的 Skill 可按主题分组。每个包必须包含同时面向 Codex 和 Claude Code 的
`SKILL.md`，并可按需包含 `references/`、`scripts/` 和 `assets/`。与平台绑定的
配置不放入主说明：Codex 的界面元数据可放在 `agents/openai.yaml`；Claude Code 的
插件元数据在需要以插件方式分发时放入根目录 `.claude-plugin/`。某个主题首次拥有
已发布 Skill 时，再为该主题创建 README 作为分类入口。

## 对外文档

根目录 README 使用中英双语，说明仓库用途、目录职责、跨 Codex / Claude Code 的
Skill 包约定和本地验证方式。`CONTRIBUTING.md` 说明如何提交新的 Skill 或文档变更。
`CLAUDE.md` 提供 Claude Code 读取的仓库协作指引；Codex 继续使用已有的 `AGENTS.md`。
`.gitignore` 排除本地编辑器文件、凭据、大型生成物，以及本仓库的 `archive/` 工作区，
防止误提交。

## 首版范围

首个公开版本只包含目录结构、说明文档、许可证和 Git 元数据；不包含具体 Skill、
Claude Code 插件清单、发布自动化、包管理配置、Changesets 或 CI 工作流。这些能力
只在真实 Skill 出现相应需求时引入。

## 验证方式

发布前确认必需目录和文档均存在、README 中的链接可访问、被忽略的材料未被暂存，
且首次公开提交干净无多余文件。最后确认 GitHub 仓库为公开状态，默认分支为 `main`。
