---
name: handbook-parser
description: 把 RDK 课程讲义 markdown 解析为结构化 slide blueprint（JSON）。识别讲义顶部元信息、配套资源、目标章节、关键概念、详细讲解、常见问题、拓展练习等模块，逐段映射到对应的 slide pattern（cover / cards-3 / cards-4 / cards-6 / split-checklist / split-timeline / code-highlight / resource-list / flow-5 / closing）。当用户提供讲义 md 并希望生成课件蓝图时使用；不用于讲义内容审校，也不用于 HTML 生成本身。
---

# 讲义解析为 Blueprint

## 目标与边界

- 完成：把一份 RDK 小课堂讲义 md 文件解析为完整的 slide blueprint JSON，覆盖从封面到收尾的每一张 slide。
- 不处理：讲义内容改写、章节合并、HTML 渲染。若讲义里某段表述不清或章节缺失，**在 blueprint 中标记 `"needs_review": true`** 后继续，不擅自润色。

## 触发与反触发

| 情形 | 行为 |
|---|---|
| 用户提供讲义 md，请求生成 HTML | 先跑本 Skill 出 blueprint |
| 用户已有 blueprint，只想改一小段 | 走 Edit 工具直接改 blueprint JSON，不重跑 parser |
| 用户想从已有 HTML 反向抽 blueprint | 不支持，反问用户提供原始 md |

## 输入与前置条件

- 必需：讲义 md 文件绝对路径。
- 预检：
  1. 文件存在且非空；
  2. 顶部有明确的课程标题（首个 `#`）；
  3. 至少 3 个 `##` 顶层章节；否则文件过于简略，报告需要用户补充。

## 产物与完成标准

- 产物：`<course-name>-blueprint.json`（默认写到讲义同目录，或用户指定路径）。
- 完成：JSON 通过 `handbook-schema.md` 定义的字段校验（meta.title / meta.lang / meta.logo_key / slides[] 每项有 pattern + kicker + title）。

## 执行流程

1. **读元信息**：抽出讲义顶部到第一个 `##` 之前的表格/段落，识别`适用板卡`、`系统版本`、`预计时间`、`课程目标` → 生成第 1 张 `cover` slide。
2. **识别配套资源**：查找`**配套资源**`附近的列表，若存在则生成一张 `resource-list` slide 放在开头前 3 页内。
3. **遍历 `## N.` 章节**，按 `references/handbook-schema.md` 的映射表决定 pattern：
   - 有表格且 3-4 行 → `cards-3` / `cards-4`
   - 表格 5-8 行 → `cards-6` 或 `cards-4`（截断/合并）
   - 列表 ≥4 项，无子标题 → `split-checklist`
   - 列表带步骤感（Step 1/2/3 或"第一步/第二步"）→ `split-timeline`
   - 章节含 `\`\`\`bash` 代码块 → `code-highlight`
   - 章节是流程串联 → `flow-5`
   - 子章节 ≥3 个 → 每子章节 1 张 slide
4. **每张 slide 内**填字段：
   - `kicker`：从章节标题映射成英文短语（查 `i18n-glossary.md` 的 kicker 表）
   - `title`：讲义原标题去掉编号，若超 14 字则重写为凝练版
   - `lead`：可选，抽章节开头 2-3 行说明
   - `cards[]` / `steps[]` / `items[]`：从表格/列表/代码块抽出
   - `icon`：查 `icon-vocabulary.md` 的"语义匹配建议"
   - `tint`：查 `design-system.md` §6"分配原则"，同 slide 内 3 张卡用不同 tint
5. **末尾**：若讲义末尾有"下一课..."一段 → 生成 `closing` slide；否则用课程总结 `cards-4`。
6. **附录不入 slide**（附录 A/B/C 是查阅资料，slide 放不下）。
7. **写 blueprint 到磁盘**，同时打印摘要（slide 数、每张的 pattern + title）。

## 验证

- **阶段验证**：每张 slide 生成后立刻检查有 kicker + title + pattern 三项。
- **最终验证**：
  1. slide 数量通常在 8-18 之间；有独立教学章节、配套资源或收尾页时可扩展到 20。少于 8 说明覆盖不全，多于 20 说明拆得太碎；
  2. 相邻 slide 的 pattern 不完全一样（避免连续 5 张都是 cards-3）；
  3. 每张 title 汉字数 ≤ 14 / 英文字符数 ≤ 32；
  4. JSON 可被 `json.loads` 解析；
  5. 每个 slide 的 icon key 都在 `icon-vocabulary.md` 表内。
- **证据保存**：把摘要输出（slide 总数、每张 title 一览）打印在会话里。

## 失败处理

- **讲义章节太少**（<3 个 `##`）：报告"讲义结构过于简单，请补齐至少 3 个主要章节再重试"。
- **表格解析失败**（行数不一致、格式错乱）：跳过该章节生成默认的 `cards-3` 骨架 + `"needs_review": true`。
- **图标 key 找不到**：先在 `icon-vocabulary.md` 里手动加一条，或选一个语义最接近的通用图标。
- 同一策略最多重试 2 次。第二次仍失败 → 保存中间结果、报告哪张 slide 卡住、请用户手动编辑 blueprint。

## 风险与确认

- 风险等级：`low`（只读 md，只写 blueprint JSON）。
- 若 blueprint 文件已存在 → 提示用户是否覆盖或保存为 `<name>-v2.json`。

## 按需参考

- 讲义章节 → slide pattern 映射 → 读 `references/handbook-schema.md`。
- 挑图标 → 读 `references/icon-vocabulary.md`。
- 分配 tint → 读 `references/design-system.md` §6。
