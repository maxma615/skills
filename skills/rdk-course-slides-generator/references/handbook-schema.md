# 讲义 → Slide 映射规则

> 输入：一份 RDK 小课堂讲义（markdown）。输出：一份 slide blueprint（每张 slide 的 pattern + 内容）。

## 讲义典型章节

RDK 小课堂讲义通常有以下顶层章节（`#` 或 `##` 标题）：

| 讲义章节 | 常见标题模式 | 建议 slide |
|---|---|---|
| 元信息头 | 适用板卡 / 系统版本 / 预计时间 / 课程目标 | `cover` |
| 配套资源 | "配套资源"、"课程资料" | `resource-list` |
| 本课要解决什么问题 | "1. 本课要解决什么问题" | `cards-3` |
| 本课完成后你能做到什么 | "2. 本课完成后你能做到什么" | `split-checklist` |
| 开始前确认 | "3. 开始前确认" | `resource-list`（如果是资源清单）或 `cards-3` |
| 先看整体资源地图 | "4. 先看整体资源地图" | `cards-3`（每个模块 1 张卡）或 `cards-6` |
| 关键概念 | "5. 关键概念快速说明" | `cards-4` 或 `cards-6` |
| 详细讲解主体 | "6. 各模块详细说明" | **每小节 1 张 slide**，根据子节数选 cards-3/cards-4 |
| 论坛与社区（子章节多） | 提问平台 / 三件事 / 排查四步 / 提问模板 | 每子节 1 张 slide |
| 完成判断 | "8. 如何判断本课完成" | `split-checklist` |
| 常见问题 | "9. 常见问题与排查" | `cards-3` 或 `cards-4`（每个 Q&A 1 张卡）|
| 本课小结 | "10. 本课小结" | `cards-4`（4 个记忆点）或 `cards-6` |
| 拓展练习 | "11. 拓展练习" | `split-checklist`（当作 3-4 个任务列表） |
| 附录 | "附录 A/B/C" | 通常不上 slide（讲义里查即可） |
| 下一课预告 | 讲义末尾"下一课..."一段话 | `closing` |

## 解析步骤

1. **提取元信息**：读讲义顶部到第一个 `##` 之前的元数据，抽 `适用板卡` `系统版本` `预计时间` `课程目标`，用于 cover 的 kicker + lead。
2. **抽出 `## N. 标题`**（顶层章节）：每个变成一张或多张 slide。
3. **章节内含 `###` 子章节**：如果 ≥3 个平级子章节，本 slide 用 `cards-3` / `cards-4` / `cards-6`；如果 ≤2 个子章节，合并为一张 `split-*` slide。
4. **章节内有表格**：表格通常是"关键词 / 说明"结构 —— 每行变成一张 card。
5. **章节内有代码块**：如果这一节包含命令行块 → 用 `code-highlight` pattern。
6. **章节内有列表 ≥4 项**：用 `split-checklist`。
7. **章节内是流程**（"第一步 → 第二步 → ..."）：用 `split-timeline` 或 `flow-5`。

## 章节转 slide 的完整示例

### 输入片段：

```markdown
## 5. 关键概念快速说明

|概念|说明|
|---|---|
|RDK|Robotics Development Kit，...|
|BPU|Brain Processing Unit，...|
|miniboot|RDK 的引导程序...|
|tros|TogetheROS.BOT，...|
```

### 生成 blueprint slide：

```json
{
  "pattern": "cards-4",
  "kicker": "Concepts",
  "title": "几个关键词先认识",
  "cards": [
    {"tint": "tint-1", "icon": "chip",     "title": "RDK",      "body": "Robotics Development Kit，..."},
    {"tint": "tint-2", "icon": "brain",    "title": "BPU",      "body": "Brain Processing Unit，..."},
    {"tint": "tint-4", "icon": "wrench",   "title": "miniboot", "body": "RDK 的引导程序..."},
    {"tint": "tint-6", "icon": "robot",    "title": "tros",     "body": "TogetheROS.BOT，..."}
  ]
}
```

**图标怎么选**：查 `icon-vocabulary.md` 的"语义匹配建议"表。若关键词不在表里，选一个语义最接近的通用图标（比如"文档中心"→ `layers`；"论坛"→ `message`）。

## 每张 slide 的字段填法

### kicker（英文小标签）

- 中文页也用英文 kicker（这是 Apple keynote 风格）。
- 从讲义章节含义映射，用简短 2-4 词：
  - "1. 本课要解决什么问题" → `Why This Course`
  - "2. 完成后你能做到什么" → `What You'll Learn`
  - "6.1 官方文档手册" → `Documentation`
  - "7.4 基础排查四步" → `Baseline Debug`
  - "10. 本课小结" → `Summary`

### title（h2 中文标题）

- 尽量直接用讲义里的章节标题（去掉编号）。
- 保证一行 —— 若原标题超 14 个汉字，改为更凝练的版本（比如"发帖前先做三件事" 而不是"发帖之前建议先做以下三件事"）。

### lead（副标题段）

- 可选。若讲义原节开头有一段 2-3 行的说明段，抽出精简为 lead。
- 若原节直接就是列表/表格没有说明段，lead 可留空。

### body（card 里的说明）

- 保留讲义原文的核心信息，一句话概括，≤40 字。
- 不要照搬讲义原文长句 —— 卡片是"视觉锚"不是"完整段落"。

## 保留讲义原文的部分

- 命令行块（`\`\`\`bash ... \`\`\``）**必须逐字保留**，进入 `code-highlight` pattern 的 `code` 字段。
- 链接 URL 必须原样保留，进入 `resource-list` pattern 的 `href` 字段。
- 数字、版本号、板卡型号必须原样保留。

## 不能上 slide 的内容

以下讲义内容**不生成 slide**：

- 附录 A/B/C（长模板、社区规范条款、资源速查表）—— 这些是"手边查"用途，slide 上放不下也没必要。
- 单独一行的过渡引导（"下面我们看..."、"我们来看看..."）。
- 与前一节完全重复的信息。

## 校验

生成 blueprint 后必须回头检查：
1. slide 数量与讲义章节数量对应关系是否合理（1 章 = 1~2 张 slide 为佳，不超 3 张）；
2. 相邻 slide 的 pattern 是否有变化（避免连续 5 张都是 cards-3 造成视觉疲劳，可穿插 split-checklist / split-timeline）；
3. 所有 slide 的 title 是否 ≤14 汉字或 ≤32 英文字符（长会被 nowrap 截断）；
4. 每张 slide 至少有 kicker + title 两项，否则视为无效。
