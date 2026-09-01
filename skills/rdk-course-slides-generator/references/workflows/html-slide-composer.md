---
name: html-slide-composer
description: 把 slide blueprint JSON 组合成完整的 Apple 风格视频演示 HTML。应用 design-system.md 里的字体栈、缓动、6 色 tint、Lucide SVG 图标，输出单文件自包含 HTML（logo base64 内嵌，无外部依赖）。当已有一份 blueprint 需要渲染为 HTML 时使用；不用于讲义解析或视觉走查。
---

# Blueprint 组合为 HTML

## 目标与边界

- 完成：读取 blueprint JSON，输出一份符合 design-system 规范的单文件 HTML（体积 <100KB 含内嵌 logo）。
- 不处理：内容层修改（内容问题回到 handbook-parser 或用户手改 blueprint）、多语翻译（用 bilingual-variant）、发布/上传。

## 触发与反触发

| 情形 | 行为 |
|---|---|
| 有 blueprint JSON，需要生成 HTML | 使用本 Skill |
| 只想改 HTML 里一个词/一个色 | 用 Edit 直接改 HTML，不重跑 composer |
| 需要中英双版本 | 先 `bilingual-variant` 出英文 blueprint，再本 Skill 跑两次 |

## 输入与前置条件

- 必需：
  - blueprint JSON 路径
  - 目标语言 `cn` / `en`
  - 输出 HTML 路径
- 预检：
  1. blueprint JSON 可解析、通过 `handbook-schema.md` 的字段校验
  2. `meta.logo_key` 对应的 PNG 存在于 `assets/`
  3. 每张 slide 的 `icon` key 都在 `icon-vocabulary.md` 表内
  4. 输出目录可写
  5. 若输出文件已存在，展示"将覆盖 <path>"并请求确认；除非用户明确要求，否则保留旧文件为 `<name>.bak.YYYYMMDD.html`

## 产物与完成标准

- 产物：一份完整 HTML 文件。
- 完成：
  1. 文件大小 20-80 KB（正常范围，logo base64 占 ~30KB）
  2. `data:image/png;base64` 出现 1 次（logo 内嵌成功）
  3. `assets/` 引用出现 0 次（完全自包含）
  4. `<html>` 到 `</html>` 完整闭合
  5. slide 数量与 blueprint 中一致

## 执行流程

1. **加载 blueprint**，校验字段完整性。
2. **加载 design-system.md 与 slide-patterns.md**：把常量（字体栈、缓动、tint 色板）注入 HTML 的 `<style>`。
3. **加载对应 logo PNG**，转 base64 data URI，作为 `<img class="brand-logo" src="data:...">` 属性。
4. **加载 icon-vocabulary.md**，构建 `icon_key → svg_inner` 字典。
5. **按语言选字号档**：cn 用中文档，en 用英文档（缩 15-20%）。
6. **遍历 slides**，每张 slide 按 `pattern` 找对应 HTML 模板函数，代入 blueprint 字段生成 `<section class="slide">` 片段。
7. **组装完整 HTML**：`<head>` + `<style>` + `<body><main class="deck">` + slides + 导航条 + `<script>`。
8. **写文件**：utf-8、无 BOM。
9. **打印摘要**：文件大小、slide 数、logo 类型、验证项 pass/fail 一览。

## 验证

- **阶段验证**：每张 slide 生成后串接前，使用当前平台的文本搜索确认存在 `data-title` 和 h2 元素。
- **最终验证**：
  - `data:image/png;base64` 出现 = 1
  - `assets/` 出现 = 0
  - `data-title=` 出现次数 == blueprint slide 数
  - `</html>` 出现 = 1
  - 文件大小 20 < size < 100 KB
- **证据保存**：把上述指标写入返回消息。

## 失败处理

- **blueprint 字段缺失**（如缺 `title` 或 `icon`）：报告缺失项、指出 slide 索引，请用户补齐后重试。
- **图标 key 不在 vocabulary**：先在 `icon-vocabulary.md` 加一条，或改用最接近的通用图标；重试 1 次。
- **文件写入失败**：检查磁盘/权限。同一策略最多重试 2 次。
- **生成 HTML 大小异常**（>200KB 或 <10KB）：可能 base64 出错或 slide 空，报告排查。

## 风险与确认

- 风险等级：`medium`（会覆盖对外发布的 HTML）。
- 确认点：
  1. 目标文件已存在 → 明确说"将覆盖 <path>"，在用户确认后执行；若需要保留旧版，先由调用方另存为 `<path>.bak.YYYYMMDD.html`。
  2. logo 变更 → 展示新旧 logo 尺寸和 base64 摘要，用户确认。
- 恢复方式：仅当调用方在覆盖前创建了 `.bak` 文件时，才能从该备份复原；`build-html.py` 本身不会自动备份。

## 按需参考

- 样式常量（字体/缓动/tint）→ `references/design-system.md`
- HTML 结构模板 → `references/slide-patterns.md`
- 图标 SVG → `references/icon-vocabulary.md`

## 实现建议

优先直接调用 `scripts/build-html.py`（本 Pack 提供的参考实现）：

```sh
python scripts/build-html.py --blueprint <path-to-blueprint.json> --lang cn --output <path-to-output.html>
```

该脚本封装了上述所有步骤。若需要视觉微调，改 script 优于让 Skill 每次现场写 HTML 字符串。
