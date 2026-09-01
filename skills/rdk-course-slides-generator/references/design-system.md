# 设计系统

> 本 Pack 所有 HTML 都必须严格遵守。修改本文件属于高风险操作——任何一次调整都会影响未来所有课件。

## 1. 地瓜品牌色板（官方规范）

### 核心标准色

| 名称 | HEX | RGB | CMYK | CSS 变量 |
|---|---|---|---|---|
| 核心橙 | `#FF3C00` | `255, 60, 0` | `0, 87, 94, 0` | `--brand` |

单色物料统一使用 `#FF3C00`，是整个 RDK 视觉体系的**唯一主色**。任何 CTA 按钮、进度条、kicker、accent 文字都从这里衍生。

### 品牌渐变

| 名称 | 起点 | 终点 | 用途 |
|---|---|---|---|
| 黑客松渐变橙 | `#FF6200` → `#FF0900` | 主 hero、活动物料 | 承载"活动感"的强渐变 |
| 全谱橙渐 | `#FF0900` → `#FF3C00` → `#FF6200` → `#FFAE00` | h1 里的 `.gradient` span、进度条 `.bar` | 承载"课程感"的柔和渐变，落在深红到暖金 |

对应 CSS：

```css
/* 黑客松强渐变（4 色停）*/
background: linear-gradient(135deg, var(--brand2), var(--brand3));

/* 全谱渐变（4 色停，用于 gradient text 和 progress bar）*/
background: linear-gradient(90deg, var(--brand3), var(--brand), var(--brand2), var(--o5));
```

### 辅助色系列（橙色衍生色，与核心橙一起构成完整色环）

| 名称 | HEX | RGB | CSS 变量 | 建议用途 |
|---|---|---|---|---|
| 核心橙 | `#FF3C00` | `255, 60, 0`   | `--brand`  | 主色，logo 圆点、CTA、accent |
| 品牌深红 | `#FF0900` | `255, 9, 0`   | `--brand3` | 渐变起点、强调色 |
| 品牌橙 2 | `#FF6200` | `255, 98, 0`  | `--brand2` | 渐变终点、按钮渐变 |
| 辅色 O1 | `#FF5500` | `255, 85, 0`  | `--o1` | tint 变体的暖橙 |
| 辅色 O2 | `#FF7300` | `255, 115, 0` | `--o2` | 图表/装饰环第二色 |
| 辅色 O3 | `#FF8C00` | `255, 140, 0` | `--o3` | 章节标签底色变体 |
| 辅色 O4 | `#FF9D00` | `255, 157, 0` | `--o4` | 图标高亮 |
| 辅色 O5 | `#FFAE00` | `255, 174, 0` | `--o5` | 全谱渐变的暖金终点 |

### 使用规则

- **单色**：任何仅用一种颜色时都用 `#FF3C00`（品牌核心橙）。不要私自换成 `#FF5500` 或 `#FF6200` "近似替代"。
- **双色渐变**：黑客松风格用 `#FF6200 → #FF0900`（135deg 强渐变，反差大）；课程风格用 `#FF0900 → #FF3C00 → #FF6200 → #FFAE00`（90deg 全谱柔渐变）。
- **辅助色**：`--o1..o5` 系列用在装饰环、图表节点、tint 变体、图标高亮等**次要视觉元素**。不用于主标题、主 CTA。
- **背景径向光晕**：常用 `rgba(255, 60, 0, .13)`（右上）+ `rgba(255, 174, 0, .13)`（左下）叠加浅底渐变。
- **文字色**：品牌橙 `#FF3C00` 仅用于短促标签（kicker、tag、accent 词）；正文永远用 `#111` / `#3a3a3d` / `#6e6e73` 三级灰。

### 无障碍与对比度

- 品牌橙 `#FF3C00` 在纯白 `#FFFFFF` 底上对比度 3.6:1，**仅适合 ≥18px 大号文字或图形元素**。用于小号正文时颜色需切成 `#111`。
- 品牌橙 `#FF3C00` 在浅底半透明卡片 `rgba(255,255,255,.78)` 上略衰减，仍达到大字最低对比要求。

## 2. 文字与灰阶

```css
--text:  #111111;   /* 主标题 h1/h2 */
--muted: #6e6e73;   /* 说明段、次要文字 */
--line:  rgba(17, 17, 17, .10);   /* 卡片边框、分割线 */
```

三级文字：主 `#050505`（h1/h2）→ 次 `#3a3a3d`（card p）→ muted `#6e6e73`（说明段）。

## 3. 字体栈

```css
--font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
             "PingFang SC", "HarmonyOS Sans SC", "MiSans",
             "Microsoft YaHei UI", "Microsoft YaHei", "Myriad Pro", sans-serif;
--font-mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
```

feature settings（SF Pro 特性）：`font-feature-settings: "ss01", "ss02", "cv11"` + `font-variant-numeric: tabular-nums`。

## 4. 字号系统

### 中文版（默认）

| 元素 | clamp | weight | letter-spacing |
|---|---|---|---|
| h1 | 40/4.8vw/78 px | 720 | -0.036em |
| h2 | 34/3.8vw/58 px | 720 | -0.028em |
| h3 | 19/1.6vw/27 px | 640 | -0.012em |
| p/li | 16/1.2vw/21 px | 400 | -0.006em |
| .lead | 19/1.5vw/27 px | 400 | -0.010em |
| .kicker | 13px 固定 | 640 | .18em uppercase |

**h1/h2 用 `white-space: nowrap`**（保证一行）；窄屏 media query 里放开为 normal。

### 英文版（缩 15-20%）

| 元素 | clamp | weight | letter-spacing |
|---|---|---|---|
| h1 | 40/4.6vw/76 px | 720 | -0.036em |
| h2 | 32/3.4vw/54 px | 720 | -0.028em |
| h3 | 19/1.55vw/26 px | 640 | -0.012em |
| p/li | 16/1.2vw/20 px | 400 | -0.006em |
| .lead | 18/1.45vw/25 px | 400 | -0.010em |
| .kicker | 13px 固定 | 640 | .16em uppercase |

**h2 用 `white-space: normal`**（英文长标题允许折 2 行）。

## 5. 动效缓动

```css
--ease-out-expo: cubic-bezier(0.22, 1, 0.36, 1);
--ease-out-back: cubic-bezier(0.34, 1.4, 0.64, 1);
```

- **翻页进入**：`opacity .8s + transform .8s (Y+28 → 0, scale .985 → 1) + filter .6s (blur 4 → 0)`，全部用 `ease-out-expo`。
- **翻页离开**：`opacity/transform/filter .38s`，同样缓动，`Y 0 → -24`。
- **内部元素错峰入场**：`slide-inner > *` 依次 delay 80/180/280/380/480ms；grid/path/checklist/timeline 子项再依次 delay 280/360/440/520/600/680ms。
- **禁用条件**：`@media (prefers-reduced-motion: reduce)` 全关，只保留 120ms 淡入。

### 5.1 动效边界、性能与可访问性

- **翻页定位**：翻页是用于讲解节奏的解释性动效，可以使用既有 800ms 入场；不得阻塞导航，也不得让离场、入场状态叠加。
- **动效目的**：每个动效必须服务于解释、空间连续性、状态提示、反馈或避免突兀变化；没有明确目的的循环装饰动效禁止使用。
- **属性边界**：进入与离开只组合 `opacity` 和 `transform`；禁止 `transition: all`、`ease-in`、`scale(0)` 以及 `width`、`height`、`margin`、`padding`、`top`、`left` 等布局属性动画。
- **缓动选择**：`--ease-out-expo` 是进入与离开的默认曲线；命名的强 ease-in-out 仅用于屏上位移动画；`linear` 仅用于进度指示。
- **错峰限制**：内部错峰只在首次入场使用，以帮助理解内容层级；不得制造持续动效，也不得拖慢键盘导航。
- **可访问性**：`prefers-reduced-motion` 模式保留短暂 `opacity` 变化，移除位移、缩放、模糊与错峰；如引入 hover 动效，必须置于 `@media (hover: hover) and (pointer: fine)` 内。

## 6. 6 色 tint 池（主题卡）

用于 `.card.themed`。每张卡通过 `class="card themed tint-X"` 应用。

| class | 底纹（135deg 渐变） | 标题色 --accent |
|---|---|---|
| tint-1 | rgba(255,68,0,.14) → rgba(255,255,255,.6) | #E53500（红橙）|
| tint-2 | rgba(255,140,0,.14) → rgba(255,255,255,.6) | #C96500（琥珀）|
| tint-3 | rgba(255,196,0,.16) → rgba(255,255,255,.6) | #A67200（金）|
| tint-4 | rgba(112,196,255,.16) → rgba(255,255,255,.6) | #0A6DBF（蓝）|
| tint-5 | rgba(140,120,255,.14) → rgba(255,255,255,.6) | #5A46C7（紫）|
| tint-6 | rgba(80,200,150,.14) → rgba(255,255,255,.6) | #158961（绿）|

**分配原则**：同一 slide 内 3 张卡用 3 个不同 tint；6 张卡时用完整色环。跨 slide 保持"暖色（1-3）优先给上手/多媒体/开始类，冷色（4-6）优先给 AI/驱动/结束类"的语义直觉。

## 7. 卡片规格

```css
.card {
  padding: 25px;
  border-radius: 28px;
  background: rgba(255,255,255,.78);
  border: 1px solid var(--line);
  min-height: 128px;
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
  backdrop-filter: blur(18px);
}
.card.themed { padding: 28px 26px 24px; }
.card.themed .card-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  background: rgba(255,255,255,.9);
  color: var(--accent);   /* 图标颜色跟随卡片主色 */
  margin-bottom: 18px;
}
.card.themed .card-icon svg { width: 28px; height: 28px; }
.card.themed h3 { color: var(--accent); font-weight: 720; }
```

英文版整体 padding 缩：`.card { padding: 22px }`、`.card.themed { padding: 24px 22px 20px }`、icon pill 44×44。

## 8. Logo 使用

- 中文 HTML：右上角内嵌 `assets/logo-cn.png`（横版 D + 橙圆 + 地瓜机器人）
- 英文 HTML：右上角内嵌 `assets/logo-en.png`（横版 D + 橙圆 + D-Robotics）
- **必须 base64 内嵌**：读取 PNG 二进制、编码 base64、以 `src="data:image/png;base64,..."` 写入 `<img class="brand-logo">`。
- CSS 高度：`.brand-logo { height: 44px; }`，窄屏 34px。
- 定位：`position: fixed; right: 34px; top: 24px; z-index: 20; pointer-events: none;`
- 光感：`filter: drop-shadow(0 6px 14px rgba(0,0,0,.08))`

## 9. 键盘导航（每份 HTML 都要有）

- ← / PageUp：上一页
- → / Space / PageDown：下一页
- Home：首页
- End：末页
- 1–9：直接跳该编号 slide
- `transitioning` 锁：避免快速点击导致 leaving 状态叠加错乱

## 10. 底部通用元素

- 左下 `.hint`：键盘操作提示（中文写全，英文写 "Keyboard: ← / → / Space to navigate"）
- 右下 `.nav`：`‹`  `1 / N`  `›` 三件套
- 底部 `.bar`：4px 高进度条，宽度 = 当前页 / 总页数

## 11. 禁用清单

- ❌ emoji（都替换为 Lucide SVG）
- ❌ 外部 CDN 引用（除 SF 系统字体外）
- ❌ `<br>` 用于标题折行（用 `text-wrap: balance` 交给浏览器）
- ❌ 大 `.quote` 块作为唯一内容（视觉太空，用主题卡组合替代）
- ❌ Rockwell / 衬线字体作为主字体
