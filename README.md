# Max.Ma Skills

[English](#english) | [中文](#中文)

## 中文

这是 Max.Ma 维护的跨代理 Skills 仓库，面向 Codex 与 Claude Code。它用于沉淀可复用的工作流、领域知识和工具约定。

### 目录

- `skills/`：可安装的 Skill 包。目前发布 `rdk-course-slides-generator`、`rdk-model-zoo-demo-review`、`rdk-x5-toolchain-quantization` 和 `rdk-yolo-toolkit`。
- `projects/`：Skill 开发过程中的项目说明、设计和验证材料。
- `shared/`：多个 Skill 可复用的参考资料、脚本和资产。
- `templates/`：新建 Skill 项目的起始模板。
- `archive/`：本地历史材料和大型临时文件，不纳入版本控制。
- `sources/`：第三方 Skills 的官方来源与安装说明；不镜像其正文。
- `scripts/`：在 Windows 和 WSL 上安装本仓库个人 Skills 的辅助脚本。

### Skill 包约定

每个公开 Skill 以 `SKILL.md` 为必需入口，可按需包含 `references/`、`scripts/`、`assets/`。`agents/openai.yaml` 可提供 Codex 专属界面元数据；需要作为 Claude Code 插件分发时，再添加 `.claude-plugin/` 元数据。

贡献和本地验证方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 多设备同步

在新设备克隆本仓库后，使用下列脚本安装个人 Skills。默认不会覆盖已存在的本地版本；确认要以仓库内容替换时添加 `-Force` 或 `--force`。

```powershell
.\scripts\install-personal-skills.ps1 -Target all
```

```sh
./scripts/install-personal-skills.sh --target all
```

第三方 Skills 的官方来源与安装入口见 [sources/third-party-skills.md](sources/third-party-skills.md)。Hermes 内置或可选 Skills 不由本仓库管理。

### 许可与品牌

仓库代码和文档适用 MIT 许可证；RDK 课件 Skill 中的品牌素材、Logo 与示例例外，使用前请阅读 [NOTICE.md](NOTICE.md)。

## English

This is Max.Ma's cross-agent Skills repository for Codex and Claude Code. It collects reusable workflows, domain knowledge, and tool conventions.

### Layout

- `skills/`: Installable Skill packages. It currently publishes `rdk-course-slides-generator`, `rdk-model-zoo-demo-review`, `rdk-x5-toolchain-quantization`, and `rdk-yolo-toolkit`.
- `projects/`: Project briefs, designs, and validation material for Skills in development.
- `shared/`: References, scripts, and assets shared by multiple Skills.
- `templates/`: Starter material for new Skill projects.
- `archive/`: Local historical material and large temporary files; excluded from version control.
- `sources/`: Official sources and install guidance for third-party Skills; their contents are not mirrored.
- `scripts/`: Helpers for installing this repository's personal Skills on Windows and WSL.

### Skill package contract

Every published Skill has a required `SKILL.md` entry point and may include `references/`, `scripts/`, and `assets/`. `agents/openai.yaml` may provide Codex-specific UI metadata. Add `.claude-plugin/` metadata only when distributing Skills as a Claude Code plugin.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution and local validation guidance.

### Multi-device sync

Clone this repository on a new device, then run the applicable installer. Existing local Skills are preserved by default; use `-Force` or `--force` only when the repository version should replace them.

```powershell
.\scripts\install-personal-skills.ps1 -Target all
```

```sh
./scripts/install-personal-skills.sh --target all
```

See [sources/third-party-skills.md](sources/third-party-skills.md) for upstream third-party Skills. Hermes runtime and optional Skills are intentionally unmanaged.

### License and marks

Repository code and documentation use MIT, except for the branded assets, logos, and examples in the RDK course Skill. Read [NOTICE.md](NOTICE.md) before reusing them.
