# 风格参考：Google for Developers 讲解视频（2026-10-22 调研）

> 下文是迁入本 Skill 的风格笔记原文。表里点名的 JPG 总览图没有随包发布，文字记录是风格依据。

## 实际看过的素材
我用 yt-dlp 下载了 3 个视频的 480p 无声版，用 ffmpeg 抽帧拼成总览图，逐张看过：
| 视频 | 文件 |
|---|---|
| Scaling AI with Google Cloud's TPUs — https://www.youtube.com/watch?v=8zBaa20mvoc | 每 10 秒一帧：`sheet_8zBaa20mvoc_tpu-scaling.jpg`；8 个关键帧：`frames_tpu_detail.jpg`；96–108 秒、176–188 秒每秒一帧：`motion_tpu_96-108s.jpg`、`motion_tpu_176-188s.jpg` |
| Tensor Processing Units: History and hardware（AI Adventures）— https://www.youtube.com/watch?v=MXxN4fv01c8 | 每 10 秒一帧：`sheet_MXxN4fv01c8_tpu-history.jpg` |
| Deploy Android on-device AI with ML Kit GenAI and LiteRT-LM — https://www.youtube.com/watch?v=Z7zx_sTbFPI | 每 28 秒一帧：`sheet_Z7zx_sTbFPI_litert.jpg` |

抽帧做完后视频已删除，这里只保留 JPG 总览图，仅供内部参考。

## 看到的规律
1. **图形扁平，只用线框**。主要是 1–2 px 细描边的圆角矩形，几乎没有渐变和立体效果。
   - 每种部件固定一个描边颜色：蓝色是外层容器 / 芯片，黄色是 MXU，绿色是 HBM，红色是 Sparse core。
   - 文字很小，用无衬线字体，放在框内居中或靠上。
2. **用描边换色来点名**。讲到哪个部件，它的描边就从灰色换成彩色（例如 HBM 变绿、Sparse core 变红），其他部件不动。
3. **镜头推进 / 拉远**。先给全景（工作负载 → 芯片），然后平滑缓动推近到芯片内部，填满画面后停住讲解，之后再拉远回到全景。缓动是慢进慢出，没有回弹（96–108 秒那段最明显）。
4. **逐块搭建，一次一个想法**。元素按讲解顺序依次出现，比如小方块一个个飞出来拼成 4×4×4 立方体（176–188 秒）。每一步画面上只多一样东西。
5. **用半透明色带圈出范围**。在网格上铺一条蓝色或粉色的半透明带，表示“这一片 / 这个 slice”。同类元素里要强调的那几个直接上色（灰色芯片里几颗变橙）。
6. **网格表示规模**。大量相同的小单元（芯片、MAC）排成规则矩阵，用整排或整片上色表示“同时计算”。
7. **画面底部一行字幕**，比如 “Smaller slices can also be requested.”，一句话说清当前这一步。
8. **白底幻灯片**（LiteRT 视频）：大面积留白，左边粗体标题，右边一个图示或代码块。强调色只用 1–2 个（Google 蓝 + 一个品牌色），代码放在深色圆角块里。

## dg-deck `diagram` 版式借用了什么
- 图直接画在幻灯片背景上（不加白卡、边框或阴影，边缘柔和淡出）；外形是扁平圆角线框。CPU 一律用 Google 蓝，BPU 用品牌橙 #FF5A00 / #FF3C00，中性元素用灰色 #DADCE0。
- **镜头**：`camera` 让整张图平滑推近到某个区域、再拉回全景，时长约 1.1 秒，用 Material 3 的强调缓动 cubic-bezier(.2,0,0,1)。
- **聚焦**：`focus` 把非重点元素压暗到 18% 透明度；`state` / `on` 换描边和填充颜色（点名）。
- **搭建**：`show` 让元素依次上浮淡入，连线一边出现一边画出。
- **色带**：`band` 是橙色半透明圈选带，从左往右展开，和代码页的高亮行同一种语言。
- **流动**：令牌（帧 / 张量）沿路径缓动移动，可以在节点处停顿；数据连线用虚线流动表示有数据在走。
- **MAC 阵列**：点亮时按对角线逐格亮起，之后轻微呼吸，表示“大量重复的定点计算在同时进行”。
- **底部字幕**：图下方一行，跟着步骤切换，每一步一句话。
- 播完停在全景终态（全部元素显示、不压暗）。这个终态就是 `?static=1`、`?print=1`、prefers-reduced-motion 和 PNG 导出看到的画面；每次进入该页都会重播，按 R 也可以手动重播。
