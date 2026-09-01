---
name: visual-review
description: 生成后走查 HTML：检查文件大小、slide 数、logo 内嵌、H2 单行、无 emoji 残留、无 assets/ 外部引用、无 CSS 死代码、无残留占位符。逐项对照本 Skill 的验收标准输出报告。当刚生成 HTML 或用户请求视觉走查时使用；不用于自动修复问题（发现问题回到 composer 或 Edit）。
---

# HTML 视觉走查

## 目标与边界

- 完成：给定一份生成的 HTML，逐项检查是否满足本 Skill 的验收标准和 design-system 的硬约束，输出验收报告 markdown。
- 不处理：自动修复问题；PPT/PDF 生成；播放测试（浏览器实况需要人工看）。

## 触发与反触发

| 情形 | 行为 |
|---|---|
| 刚跑完 composer 想验收 | 使用本 Skill |
| 用户说"这份 HTML 有点不对，帮我看看" | 使用本 Skill |
| 用户要求发现问题后自动修 | 拒绝——只报告不修，让用户手改或走 composer |

## 输入与前置条件

- 必需：HTML 文件路径。
- 可选：对应的 blueprint JSON 路径（用于比对 slide 数、logo_key）。
- 预检：HTML 文件存在且可读。

## 产物与完成标准

- 产物：一份 markdown 验收报告 `<html-name>-review.md`，或直接在返回消息里输出。
- 完成：报告包含以下 15 项检查项及 pass/fail/warn 结果。

## 检查项清单

### A. 文件层

1. **文件存在且可读**（size > 0）
2. **文件大小**：20 < KB < 100（自包含 + 内嵌 logo 的正常范围）
3. **UTF-8 编码**，无 BOM

### B. 结构完整性

4. **`<!doctype html>` + `</html>` 闭合**
5. **`<title>` 有值**
6. **`data-title` 数量 ≥ 6**（一份合格课件至少 6 张 slide）
7. **每张 slide 有 h2**（cover 用 h1 是例外）

### C. 视觉规范

8. **`data:image/png;base64` 出现 1 次**（logo 内嵌）
9. **`assets/` 引用出现 0 次**（自包含）
10. **`ease-out-expo` 出现 ≥ 3 次**（Apple 缓动应用完整）
11. **`text-wrap: balance` 出现 ≥ 1 次**（标题排版）
12. **`prefers-reduced-motion` 出现 ≥ 1 次**（无障碍兼容）
13. **SF Pro 字体栈存在**（搜索 `SF Pro Display`）

### C.1 动效质量

14. **主要动效属性**：进入、离开和错峰应以 `transform` 与 `opacity` 为主；若动画规则涉及 `width`、`height`、`margin`、`padding`、`top` 或 `left` 等布局属性，标记为 fail。
15. **缓动与起点**：`transition: all`、`ease-in` 和 `scale(0)` 残留均为 fail；进入与离开应使用 Pack 定义的具名曲线和可见初始形态。
16. **动效边界**：扫描 `@keyframes`；持续或无明确教学目的的循环动效标记为 fail，非循环的翻页或首次入场动效标记为 manual 复核。
17. **输入与无障碍**：必须存在 `prefers-reduced-motion`；若检测到 `:hover` 动效，必须同时存在 `@media (hover: hover) and (pointer: fine)` 门禁。缺失任一项为 fail。
18. **导航状态保护**：存在 `transitioning` 锁或等价机制，避免连续快速按键翻页时离场、入场状态叠加；缺失为 fail。

### D. 反模式检查

19. **emoji 残留 = 0**：扫描 `[\U0001F300-\U0001F9FF]` 应无匹配
20. **`Rockwell` 字体残留 = 0**（历史遗留字体）
21. **占位符 `<xxx>` 残留 = 0**（`<pack-name>` 等 skill 模板占位符不能进产物）
22. **`class="next-card"` 等未定义类残留 = 0**（历史死代码）

### E. 内容对齐（若提供 blueprint）

23. **HTML `data-title` 数量 == blueprint slides 数量**
24. **HTML 里出现的 kicker 与 blueprint 一致**（抽样 3 张 slide 抽查）

### F. 视觉走查（无法机器检查，标为 "manual"）

20. **需要人工在浏览器打开**，按左右方向键翻页，确认：
    - 每张 h2 单行显示（英文允许 ≤2 行、无孤字）
    - 卡片主题色显示正常（不是纯黑白）
    - 图标 SVG 显示为线条彩色（跟随 --accent）
    - 翻页动画流畅（内部元素错峰）
    - 键盘导航（← → Home End 数字键）响应
    - 每个动效是否有明确的讲解或交互目的，而非无意义装饰？
    - 连续快速按键翻页时，是否仍然响应及时、没有过渡状态叠加？
    - 内部错峰是否帮助理解内容层级，而非延迟阅读？
    - reduced-motion 模式下，内容是否仍清晰可辨？

## 输出模板

```markdown
# 视觉走查报告：<html-file-name>

生成时间：<datetime>
输入文件：<abs-path>
文件大小：<size> KB

## A. 文件层
- [pass] 存在且非空
- [pass] 大小 32KB 在合理区间
- [pass] UTF-8

## B. 结构
- [pass] doctype 和 </html> 闭合
- [pass] slide 数：12
- ...

## D. 反模式
- [pass] emoji 残留 0 处
- [pass] Rockwell 残留 0 处
- ...

## F. 需要人工走查
- [ ] 浏览器翻页测试：翻页动画是否流畅
- [ ] 每张 h2 是否单行
- [ ] 图标颜色是否跟随卡片主色
```

Fail 项要给出**修复建议**：
- "size 118KB 超出上限" → "检查是否有多张 base64 图片未压缩"
- "emoji 残留 3 处（位置 line 245, 267, 289）" → "回到 blueprint 把这几张 slide 的 icon 换成 vocabulary 里的 SVG"
- 动效相关 fail 项按以下顺序修复：删除无必要动效 → 缩短时长、减小位移或减少属性 → 修正缓动与时长 → 修正 `transform-origin` 或初始状态。

## 执行流程

1. 打开 HTML 文件读全文。
2. 使用当前平台可用的文本搜索、regex 和字节长度检查；动效检查至少覆盖 `transition: all`、`ease-in`、`scale(0)`、布局属性动画、`@keyframes`、hover 门禁与 `transitioning` 状态保护。
3. 若提供 blueprint，做交叉检查。
4. 汇总生成 markdown 报告。
5. 返回消息里给出**总评**：通过 / 有警告可发布 / 需修复。

## 验证

- **阶段验证**：每项检查有明确 pass/fail 判定。
- **最终验证**：
  1. 报告包含至少 15 项自动检查 + 5 项人工走查提示；
  2. 所有 fail 项都有修复建议；
  3. 若全部 pass，明确写"✅ 可发布"。

## 失败处理

- 无法读取 HTML：报告文件问题，不生成报告。
- 文本搜索输出异常：可能是二进制文件误判；改用可处理 UTF-8 文本的搜索工具或 Python `re` 重跑。

## 风险与确认

- 风险等级：`low`（只读检查，不修改任何文件）。
- 无需确认。

## 按需参考

- 完成标准 → 根目录 `SKILL.md` 的“Render and validate”部分
- 设计约束 → `references/design-system.md`

## 使用建议

生成 HTML 后立即跑本 Skill，比让人肉过一遍准确。人工走查那 5 项是本 Skill 无法机器判断的（视觉流畅感），仍需要在浏览器里跑一次。
