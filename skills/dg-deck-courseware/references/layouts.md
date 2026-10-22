# dg-deck layouts

**原版恢复（10 种）**：cover, cards, section, bullets, code, flow, table, bars, links, closing。
这 10 种的 HTML 结构、CSS 和动画时序都和 `lesson-2-01.zh.html` 一致：用 `examples/lesson-2-01.zh.json` 重新构建，得到的文件和原文件逐字节相同。每种版式的原版片段在 `assets/templates/layouts/<layout>.example.html`。
**重建，非原版（8 种）**：agenda, compare, metrics, image-text, timeline, people, quote, podium。
这 8 种的 **CSS 是原版的**（`assets/templates/theme.css` 里本来就有 `.agenda/.cmp/.metric/.it/.tl/.sched/.person/.quote/.podium` 的样式，原文件只是没用到）。HTML 结构是根据这些选择器推断的，动画时序是我定的。另外 2 处 CSS 有但没有实现：`.qrs/.qr`（二维码卡片）、`.cv-meta/.cv-img`（封面的元信息行和封面图）。
**扩展（不是原版）**：`cards.dense`、`code.dense`、`code.blocks[].wide` 带 note。只要某页用到这些，build.py 才会追加 `assets/templates/ext.css`；不用时输出和原版完全一样。
动画类型（`data-a`）：rise（上浮）、fade（淡入）、pop（缩放弹出）、left（左侧滑入）、num（大数字）、draw（线条画出）、bar（条形增长）、grow（纵向增长）、type（打字）。`--d` 是延迟（毫秒）。
容量是根据原版内容和字号估算的（新版式在 gallery 里渲染核对过），不是硬性限制。超出时 `render.py` 的溢出检查会报出来。

## 原版恢复

### cover
**字段**：`eyebrow`（前面带四角星图标）；`heading`（150px，用 `==x==` 标橙色高亮，英文/数字走 Outfit 字体）；`lead`；`tags[]`（写成 `{"text","dark":true}` 是黑色胶囊）；`hero{center, caption, nodes[]}`。
**外观**：白底，右下角有一块缓慢漂移的渐变色块。左栏宽 920px，右侧是 600×600 的主视觉：白色中心圆，虚线圆环上均匀分布 n 个节点，从 12 点方向开始顺时针。不写 `hero` 时左栏变成 1600px 宽。
**容量**：有 hero 时，标题每行约 5–6 个汉字，最好只有 1 行（原版是「认识 BPU」）；lead 不超过约 60 字；节点最好 4 个，每个不超过 6 字；标签 6 个以内（单行）。

### cards
**字段**：`cols`（2/3/4）；`row:true`（图标在左、文字在右的横排卡）；`cards[]{num | icon+tone, title, text, focus, extra_html}`。tone 可选 orange、blue、green、yellow、red、grey；图标见 `assets/icons/`。
**外观**：白卡，带阴影，依次上浮出现，每张间隔 90ms。`focus` 卡有橙色内描边。
**容量**：cols-3 时每张卡说明不超过约 42 字（3 行）；cols-4 时不超过约 30 字；cols-2 横排时 4 张卡（2×2）。2 排以上的卡片要用 `dense` 扩展。

### section
**字段**：`num`、`heading`、`sub`。`toc` 可选，默认由全文所有 section 页自动生成，每项格式为「num · heading」，当前项加粗。
**外观**：左边 220px 橙色大数字，下面一条画出来的分隔线、96px 标题和副标题；右侧垂直居中放目录。没有页脚。
**容量**：标题不超过约 10 字（1000px 宽）；目录 4–6 项。

### bullets
- `variant:"split"`：左栏 700px，放 eyebrow、80px 标题、分隔线和 lead；右栏是白卡清单。条目写 `items[]{mark, text, muted, glyph}`，mark 可选 x（✕ 红）、info（→ 蓝）、note（! 灰）、check（✓ 绿，原文件没用到）、num（序号）。**容量**：最多 6 条，每条不超过约 18 字（单行）。
- `variant:"numbered"`：在页面主体里放白色横条，左边是 01–05 橙色编号。`items[]` 为字符串。**容量**：最多 5 条，每条不超过约 32 字。

### code
**字段**：`blocks[]{label, host（默认 "root@rdk: ~"）, lines[], note{k, p}}`。
**外观**：每个代码块一行，左边是 1030px 宽的深色终端（红黄绿三个圆点，橙色标题），右边是橙色竖线引出的要点。终端先弹出，然后逐行打字；`hl` 行打完后出现橙色高亮框。
**容量**：每页 2 个终端，每个最多 3 行。每行不超过约 58 个等宽字符（26px），超出会溢出终端，build 不会自动换行。要点不超过约 40 字，长的无空格词会把要点栏撑宽（原版第 19 页超出 41px）。

### flow
**字段**：`steps[]{t, s, on, num}`，列数等于步骤数。
**外观**：圆形节点（编号 01..），用虚线连接（虚线会画出来）。`on` 的节点是橙色实心。
**容量**：5 步（原版）。最多 6 步，每步 t 不超过约 7 字、s 不超过约 10 字。

### table
**字段**：`head[]`（单元格可以是字符串或 `{html, style}`）；`rows[][]`（单元格可以是字符串或 `{html, cls:"hc", colspan, style, th}`）；`row_header:true` 时第一列用 `<th>`。
**外观**：白色圆角表格，表头是浅灰底。`hc` 单元格用橙色粗体。数据行依次上浮，每行间隔 70ms，表头最后淡入。
**容量**：4 行 × 6 列，单元格不超过约 12 字（单行）。表格行高约 95px，加上 lead 时最多 5 行。

### bars
**字段**：`unit`、`dec`、`sep`、`rows[]{label, value, hi}`。`hi` 默认标在最大值那一行。
**外观**：白卡。每行依次是标签（280px）、横条和 60px 的数值。条宽 = value/max，渐变橙色，从左往右长出，数值从 0 滚动到实际值。
**容量**：4 行（原版），最多约 5 行。标签不超过约 9 个字符。

### links
**字段**：`items[]{k, d, url}`。URL 会原样显示，太长时末尾用省略号截断。
**外观**：链接卡从左依次滑入。左栏 410px 放名称，右栏放说明和灰色等宽 URL。内容区靠上对齐。
**容量**：最多 6 项（无 lead）。名称不超过约 13 字，说明单行。

### closing
**字段**：`eyebrow`（带四角星）、`heading`、`lead`、`cards[]{icon, tone, k, d, u}`、`full_logo`（默认 true）。
**外观**：浅灰底，104px 标题，3 张小卡，右下角是「地瓜机器人」完整 logo。没有页脚。
**容量**：标题不超过约 14 字；3 张卡，每张说明不超过约 20 字。

## 重建，非原版

| layout | 字段 | 外观 | 容量（实测） |
|---|---|---|---|
| agenda（重建，非原版） | `items[]{t, s, tm, num}`，`one_column` | `.ag` 白条：橙色编号、标题和副标题、右侧等宽时长。超过 3 项时排成 2 列 | 2 列时最多 8 项，t 不超过约 9 字 |
| compare（重建，非原版） | `left`/`right{badge, title, items[], good}`，`vs` | 两张白卡中间放「VS」。`good` 卡（默认右侧）有橙色描边、橙色圆点 | 每侧 4–5 条，每条不超过约 16 字 |
| metrics（重建，非原版） | `items[]{value(数字会滚动), dec, sep, pf, u, l, s}` | 大数字卡（120px，4 张时 100px），第一张数字是橙色，下面有分隔线和说明 | 3–4 张，数值不超过约 5 位 |
| image-text（重建，非原版） | `image`, `contain`, `caption`, `alt`, `text`, `items[]`, `media_right`, `placeholder` | 左边 900×560 图片卡，右边是文字和橙点列表。没有图片时显示斜纹占位 | 列表 4 项左右，text 不超过约 60 字 |
| timeline（重建，非原版） | 默认 axis：`items[]{tm, t, s, on}`；`variant:"schedule"`：`items[]{tm, t, s}` | axis：橙色渐变横轴加圆点（轴会画出来）；schedule：白卡里的时间表行 | axis 4–6 项；schedule 最多约 6 行 |
| people（重建，非原版） | `items[]{n, r, o, initials, photo, color(c2/c3)}`，`cols` | 人物卡：渐变圆形头像（显示首字或照片）、姓名、橙色职务、灰色机构 | 3–4 人 |
| quote（重建，非原版） | `quote`, `who`, `role` | 260px 橙色引号，72px 引文，分隔线，署名。没有页脚 | 引文不超过约 40 字（2 行） |
| podium（重建，非原版） | `items[]` 按名次 1/2/3 填写 `{t, w, p}`，`awards[]` | 按 2-1-3 摆放，带金银铜奖牌，台阶从下往上长出；下面一行奖项胶囊 | 3 名，t 不超过约 10 字 |

## 新增（dg-deck 扩展，原版没有）

### series-cover（新增，非原版）——系列课封面（第 1 页）
系列课（如「RDK 小课堂」）每一讲的第 1 页都用它；视频平台封面（B 站 / YouTube 缩略图）用 `scripts/render_cover.py` 从**同一组字段、同一个模板**渲染，两者像素一致，不要另做封面、也不要手改。
**字段**：
- 必填：`chapter`（章号，整数）、`chapter_name`（章名，如 `Model Zoo`）、`lesson`（课号，整数）、`title`（课名；`\n` 换行，英文长标题常用，如 `"Meet the\nBPU"`）。
- 可选：`highlight`（标题里要标橙的子串；也可在 title 里用 `==x==`）、`subtitle`（一行副标题）、`visual`（`bpu` 芯片 + MAC 阵列 | `quant` FP32→INT8 | 图片路径（相对 spec，按 contain 放进 600×600 视觉框）| `""` 不放）、`theme`（`light` 默认，系列标准样式 | `dark` | `orange`）、`badge`（右上角编号，默认 `<chapter>-<lesson 两位>`，如 `2-01`）、`series`（系列名，默认 zh「RDK 小课堂」/ en「RDK Classroom」）、`mock`（`true` 时底部加红色「MOCK-UP」条，只用于模板示意）、`nav`（导航/页脚标签，默认「封面」/「Cover」）。
- 语言跟随 `meta.lang`：`en*` 用英文字标、`Chapter N · <name> | Lesson M`，拉丁文字用 DG Sans（Outfit）；其他为中文 `第 N 章 · <章名> ｜ 第 M 课`。
**外观**：1920×1080，浅灰底（`#F4F5F7`）+ 右半部点阵和柔光；左上「地瓜机器人 | RDK 小课堂」字标，右上橙色编号胶囊；左栏 760px（x=280–1040）依次是章节行、200px 课名（highlight 部分橙色）、橙色短线、副标题；右侧 600×600 主视觉（x=1070–1670）。全部关键内容都在中间 4:3 安全区（x=240–1680）内。没有页角图标、页脚和右上角 tag。
**动画**：字标淡入 → 编号弹出 → 章节行左滑 → 课名上浮 → 主视觉弹出 → 短线画出 → 副标题上浮，约 1.1 s 播完。字体加载后若需要缩字，会重新播放一次，保证入场动画完整。静态/打印/导出/减少动效时直接显示最终画面。
**容量**：课名、副标题、章节行超出 760px 时自动缩小字号（最小 30px）；仍放不下时 `render.py` / `render_cover.py` 报 overflow。中文课名建议 ≤ 6 字；副标题 ≤ 约 16 字。
**规则**：放在第 1 页（不是第 1 页时 build.py 会警告）。未写 `meta.title` 时自动生成系列标题：`【RDK 小课堂】第 N 章 <章名> · 第 M 课｜<课名>`（en：`[RDK Classroom] Chapter N <name> · Lesson M | <title>`），与视频标题一致。
示例：`examples/series-cover.zh.json`、`examples/series-cover.en.json`。只有用到 series-cover 时才追加它的 CSS/JS；不用它的课件输出不变。

### diagram（新增，非原版）——可动画的 SVG 图解
**字段**：`eyebrow`, `heading`, `height`（SVG 高度，默认 560；宽固定 1600）, `delay`（默认 450 ms）, `caption`（静态/最终字幕，默认取最后一步）, `scene[]`, `steps[]`。
**scene 元素**（都要有唯一 `id`）：
- `box` `{x,y,w,h,label,sub,icon,kind(neutral/cpu/bpu/frame/ghost),align:"tl",mono,size,sub_size,shadow,on,r}`。`on:true` 是亮色（实心）状态。
- `text` `{x,y,text,size,weight,anchor,color(ink/ink2/ink3/orange/blue),font(mono)}`。
- `arrow` `{points[[x,y]...],mode(draw 画出 / flow 流动虚线),color(orange/blue),label,label_at,head}`。
- `token` `{x,y,label,w,h,kind(dark/light/orange),rest:"hide"}`：沿路径移动的数据胶囊。
- `band` `{x,y,w,h,label,label_at,blue}`：半透明虚线高亮带。
- `grid` `{x,y,cols,rows,cell,gap}`：MAC 阵列（会斜向扫过、脉动）。
- `bytes` `{x,y,n,kind(f32/i8),label}`。
- `images` `{x,y,cols,rows,w,h}`：校准图片缩略图。
- `photo` `{x,y,w,h,src,fit}`：实物照片（以 data URI 内嵌，路径相对 spec 所在目录）。不写 `src` 时画虚线占位框，可加 `label`。
- `meter` `{x,y,w,h,value(0–1),label,vlabel,kind(bpu/cpu/muted),label_cls}`：横向进度条。元素处于 `on` 状态时填充到 value，同时显示 vlabel（延时、使用率等）。
- `hist` `{x,y,w,h,values[],gap}`：竖向直方图，柱子从基线长出，`on` 时变成橙色（用于“量化后”）。形状只是示意，请在标签里注明。
- `levels` `{x,y,w,h,n}`：n 条等距细刻度，例如 int8 的 256 个等级。
- box 的 `kind` 新增 `bad`（红色：拒绝或报错）和 `ok`（绿色）；text 的 `color` 新增 `red`、`green`；token 的 `kind` 新增 `bad`。
**steps**：`{at(ms), show[], hide[], on[], off[], state{id:kind}, text{id:新文字}, focus[](其余变暗)/null, camera:"home"|[x,y,w,h], camdur, move[{id,path[[x,y,hold_ms]...],speed}], caption}`。构建时会检查 id 是否存在。
**外观**：图解直接画在幻灯片的渐变背景上，没有外层白卡片。SVG 四边有 22–26px 的柔和渐隐遮罩，镜头推近时不会露出硬边。
**行为**：输出的 DOM 就是最终状态，所以 `?static=1`、`?print=1`、`prefers-reduced-motion`、PNG 导出看到的都是最终画面。进入幻灯片时 JS 先重置到初始状态，再按时间轴播放；离开时回到最终状态；按 R 重播。只有用到 diagram 时，才会把 `assets/templates/diagram.css` 和 `assets/templates/diagram.js` 加进页面；不用它的课件，输出和原版逐字节相同。
**容量**：建议 ≤ 20 个元素，≤ 10 步，时间轴 ≤ 20 s。box 文字是固定像素，宽 150 的盒子放 4 个汉字（26px）。渲染器的溢出检查不会检查 SVG 内文字，需要用 `scripts/preview.py` 看帧。
**预览**：`scripts/preview.py deck.html -o preview/` 会为每个 diagram 页录制 MP4（默认 1280×720），并生成每秒一帧的 `*.frames.jpg`。
示例：gallery 第 20 页（`examples/layout-gallery.zh.json`）。大课件可以用放在该课件旁边的 `make_spec.py` 生成规格，方便重复修改。

Gallery（展示全部 18 种 + 新增 diagram）：`examples/layout-gallery.zh.json`。
