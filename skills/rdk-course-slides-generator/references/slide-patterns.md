# Slide 布局模板

> 本 Pack 只用**这 7 种**布局，不发明新的。每张 slide 的 blueprint 都必须落入其中之一（`pattern` 字段）。

---

## 1. `cover`（封面）

用途：整份课件的第一页；讲义总目录的开场。

**结构**：`split` 双列。左列 kicker + h1 + lead + tags；右列 hero panel（品牌圆 + 装饰节点）。

```json
{
  "pattern": "cover",
  "kicker": "Lesson 01",
  "title": "RDK 社区与 [gradient]生态入门[/gradient]",
  "lead": "先建立资源地图，再开始系统烧录、外设验证、模型部署与 TROS 开发。",
  "tags": ["文档入口", "GitHub 源码", "ModelZoo", "TROS", "问题反馈"],
  "hero_nodes": ["板卡上手", "模型部署", "TROS 开发", "应用实践"],
  "hero_center": {"strong": "RDK", "sub": "开发者学习路径"}
}
```

用于每份课件封面 1 张即可。第二课起 tags 可换。

---

## 2. `cards-3`（3 张主题卡）

用途：讲义里"三个方向"、"三大能力"、"三种资源"这种三分对称结构。最常用的一种布局。

**结构**：kicker → h2 → lead（可选）→ 3 张 `.card.themed` 一行铺开。

```json
{
  "pattern": "cards-3",
  "kicker": "What This Course Solves",
  "title": "这套课程解决什么问题？",
  "lead": "（可选）",
  "cards": [
    {"tint": "tint-1", "icon": "zap",    "title": "快速上手", "body": "…"},
    {"tint": "tint-2", "icon": "flask",  "title": "面向项目", "body": "…"},
    {"tint": "tint-4", "icon": "gradcap","title": "走向开发", "body": "…"}
  ]
}
```

**tint 分配**：默认给 tint-1/2/4；如果内容偏"低阶→高阶"渐进，可用 tint-1→tint-4→tint-6 呈现颜色渐进感。

---

## 3. `cards-4`（4 张主题卡）

用途：讲义里"四类内容"、"四步"、"四个组成部分"。

**结构**：与 cards-3 同，但 `.grid.cols-4`；每张卡 padding 略紧。

**tint 分配**：默认 tint-1/2/4/6，跳过 3 和 5 让色环更分散。

---

## 4. `cards-6` / `cards-8`（网格）

用途：讲义里的"6 层"、"8 个概念"、"6 种能力"。

**结构**：`.grid.cols-3` 铺 2 行。**8 卡改用 `.cols-4` 铺 2 行**。

**tint 分配**：tint-1 到 tint-6 完整循环。

**警告**：卡片数 > 8 时不再用本布局——拆成两张 slide。

---

## 5. `path-6`（学习路径）

用途：讲义里"入门→进阶→高阶→..."这种 6 步流程。

**结构**：kicker → h2 → 6 格 `.path-step`，每格左上角有大号 01-06 数字水印。

```json
{
  "pattern": "path-6",
  "kicker": "Learning Path",
  "title": "建议按这条路径学习",
  "steps": [
    {"no": "01", "title": "入门篇", "body": "…"},
    ...6 个
  ]
}
```

---

## 6. `split-checklist`（左标题 + 右 checklist）

用途：讲义"适合谁"、"完成标准"、"发帖检查清单"。

**结构**：`split` 双列。左列 kicker + h2 + lead；右列 `.checklist` 一列 4-6 项，每项 `<li>` 带 ✓ 前缀。

```json
{
  "pattern": "split-checklist",
  "kicker": "Audience",
  "title": "这门课适合谁？",
  "lead": "…",
  "items": ["第一次接触 RDK", "已有 Linux 基础", ...]
}
```

---

## 7. `split-timeline`（左标题 + 右 timeline）

用途：讲义"推荐学习方式"、"排查步骤"、"发帖流程"。

**结构**：`split` 双列。左列 kicker + h2 + lead；右列 `.timeline`：4 行胶囊徽章 + 说明。

```json
{
  "pattern": "split-timeline",
  "kicker": "How To Learn",
  "title": "推荐学习方式",
  "lead": "…",
  "steps": [
    {"badge": "Step 1", "body": "先看讲解视频…"},
    {"badge": "Step 2", "body": "打开配套讲义…"},
    ...
  ]
}
```

**徽章样式**：76×40 胶囊、橙色渐变底、`.time` class；英文版缩到 68×34。

---

## 8. `flow-5`（流程箭头）

用途：讲义里"主线：X → Y → Z → W → V"。

**结构**：`.flow` 5 个 `.step`，中间用 `::after` 伪元素画 → 箭头。

```json
{
  "pattern": "flow-5",
  "kicker": "Learning Path",
  "title": "本课主线",
  "steps": [
    {"title": "确认板卡", "sub": "X3 / X5 / S100"},
    ...
  ]
}
```

---

## 9. `code-highlight`（命令块 + 说明）

用途：讲义里"基础排查四步"这种需要展示可复制命令的页。

**结构**：kicker → h2 → lead → `.grid.cols-2`，每个 card 顶部 h3、然后一个 `.code` 命令块、下方一行 small 说明。

```json
{
  "pattern": "code-highlight",
  "kicker": "Baseline Debug",
  "title": "发帖前必做的基础排查四步",
  "lead": "…",
  "cards": [
    {"title": "① 查版本",  "code": "sudo rdkos_info",             "note": "…"},
    {"title": "② 升软件包", "code": "sudo apt update && sudo apt upgrade", "note": "…"},
    ...
  ]
}
```

**.code 样式**：`font-family: var(--font-mono); background: #fff; padding: 14px 16px; border-radius: 18px;`。

---

## 10. `resource-list`（资源入口清单）

用途：讲义末尾"核心资源速查"、导学"资源入口"。

**结构**：`.grid.cols-2` × N，每个 `.resource` 左边 strong + span、右边 `.btn`（Open 按钮）。

```json
{
  "pattern": "resource-list",
  "kicker": "Resources",
  "title": "学习时建议同步准备这些资源",
  "resources": [
    {"name": "飞书讲义", "desc": "…", "href": "#"},
    {"name": "官方文档", "desc": "…", "href": "https://developer.d-robotics.cc/rdk_doc_center/"},
    ...
  ]
}
```

---

## 11. 尾页 `closing`

**结构**：与 cover 类似但只用 kicker + h2 + lead + 3 张 cards（不是巨大的 quote 块）。

```json
{
  "pattern": "closing",
  "kicker": "Up Next · Lesson 02",
  "title": "接下来，从第二课开始",
  "lead": "…",
  "cards": [3 张主题卡预告下一课的 3 个 focus]
}
```

---

## Blueprint 顶层 schema

一份完整 blueprint JSON：

```json
{
  "meta": {
    "title": "RDK 小课堂｜第一课：RDK 社区与生态入门",
    "lang": "cn",
    "logo_key": "logo-cn"
  },
  "slides": [
    { "pattern": "cover", ... },
    { "pattern": "split-checklist", ... },
    { "pattern": "cards-3", ... },
    ...
  ]
}
```

`meta.logo_key` 可选值：`logo-cn` / `logo-en`。
`meta.lang` 决定字号系统走中文还是英文档。
