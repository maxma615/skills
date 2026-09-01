# 第三方 Skills 来源 / Third-Party Skill Sources

本仓库只发布 Max.Ma 维护的 Skills；下列上游内容不复制正文，而是记录其官方来源、许可证与安装方式。这样可以保留更新链路、避免分叉过期，并尊重原作者的分发方式。

This repository publishes only Skills maintained by Max.Ma. The upstream Skills below are not copied here. Their official sources, licenses, and installation routes are recorded instead so that they remain updateable and respect their maintainers' distribution model.

## Matt Pocock Skills

- Source: [mattpocock/skills](https://github.com/mattpocock/skills)
- License: MIT
- Installed locally: `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-me`, `grill-with-docs`, `implement`, `research`, `setup-matt-pocock-skills`, `tdd`, `to-spec`, `to-tickets`.
- Codex and other compatible agents: `npx skills@latest add mattpocock/skills`
- Claude Code managed plugin: `claude plugins install mattpocock-skills`

Choose one distribution method for a given environment. The managed plugin receives upstream updates; the `npx skills` route installs editable files.

## 飞书 / Lark Skills

- Source: [Feishu well-known Skills directory](https://open.feishu.cn/.well-known/skills/)
- Source format: `https://open.feishu.cn/.well-known/skills/<skill-name>/SKILL.md`
- Locally installed set: `lark-approval`, `lark-apps`, `lark-attendance`, `lark-base`, `lark-calendar`, `lark-contact`, `lark-doc`, `lark-drive`, `lark-event`, `lark-im`, `lark-mail`, `lark-markdown`, `lark-meeting`, `lark-minutes`, `lark-note`, `lark-okr`, `lark-openapi-explorer`, `lark-shared`, `lark-sheets`, `lark-skill-maker`, `lark-slides`, `lark-task`, `lark-vc`, `lark-vc-agent`, `lark-whiteboard`, `lark-wiki`, `lark-workflow-meeting-summary`, `lark-workflow-standup-report`.

Install or update these Skills from their official well-known URLs using the Skill manager available in the target runtime. Do not copy authenticated Lark configuration, browser sessions, or tokens into this repository.

## D-Robotics RDK and DSH Skills

| Upstream | License | Local inventory | Source |
| --- | --- | --- | --- |
| RDK Skills | Apache-2.0 | 92 Skills in WSL | [D-Robotics/rdk-skills](https://github.com/D-Robotics/rdk-skills) |
| DSH RDK plugin | Apache-2.0 | 90 bundled Skills in WSL | [D-Robotics/dsh-plugin-rdk](https://github.com/D-Robotics/dsh-plugin-rdk) |

Use the upstream README for installation and updates. The two inventories overlap substantially, so they are deliberately not mirrored here.

## Explicitly Excluded

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) and its Hermes runtime / optional Skills are not managed by this repository. They remain the responsibility of the Hermes installation and its own update mechanism.
