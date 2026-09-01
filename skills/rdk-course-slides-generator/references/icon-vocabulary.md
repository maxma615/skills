# 图标语义库

> 只使用 Lucide 风 SVG 图标。24×24 viewBox、`stroke=currentColor` 跟随卡片主色、`stroke-width=1.75px`、`fill=none`。

## 使用方式

在 blueprint 里指定 `icon` key（如 `"icon": "zap"`），composer 通过下表查到对应 SVG path。

## 图标表

| key | 语义 | SVG path (viewBox 0 0 24 24) |
|---|---|---|
| `zap` | 快速、闪电、⚡ | `<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>` |
| `flask` | 实验、试管 | `<path d="M9 3h6"/><path d="M10 3v7.5L4.9 19.1A2 2 0 0 0 6.6 22h10.8a2 2 0 0 0 1.7-2.9L14 10.5V3"/>` |
| `gradcap` | 学习、毕业帽 | `<path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>` |
| `video` | 讲解视频、播放 | `<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-6 4 6 4V8z"/>` |
| `book-open` | 讲义、书本 | `<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>` |
| `code` | 代码、Github | `<path d="M16 18l6-6-6-6"/><path d="M8 6l-6 6 6 6"/>` |
| `layers` | 官方文档、层叠 | `<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>` |
| `rocket` | 快速启动、基础环境 | `<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>` |
| `film` | 多媒体、片场 | `<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 12h20"/><path d="M6 4v16M18 4v16M2 8h4M2 16h4M18 8h4M18 16h4"/>` |
| `chip` | 硬件接口、芯片 | `<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>` |
| `brain` | 模型、神经网络 | `<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="18" r="2.5"/><circle cx="19" cy="18" r="2.5"/><path d="M12 7.5v2.5M11 11c-1.6 1-3.7 2.6-5 5M13 11c1.6 1 3.7 2.6 5 5"/>` |
| `robot` | TROS、机器人 | `<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M12 4v4"/><circle cx="12" cy="3" r="1"/><circle cx="8.5" cy="14" r="1"/><circle cx="15.5" cy="14" r="1"/><path d="M9 17h6"/><path d="M3 14H1M23 14h-2"/>` |
| `wrench` | 系统驱动、工具 | `<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>` |
| `message` | 大模型、对话 | `<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>` |
| `eye` | 感知、视觉 | `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>` |
| `arm` | 控制、机械臂 | `<path d="M12 3v9"/><path d="M12 3l4 3M12 3l-4 3"/><path d="M9 12h6l2 3v4a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2v-4z"/><path d="M9 17h6"/>` |
| `target` | 真实项目、靶心 | `<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2" fill="currentColor"/>` |
| `star` | 社区作品、星标 | `<circle cx="12" cy="9" r="6"/><path d="M8.5 13.5L7 22l5-3 5 3-1.5-8.5"/>` |
| `puzzle` | 典型应用、拼图 | `<path d="M4 4h6v3.5a1.5 1.5 0 1 0 3 0V4h6v6h-3.5a1.5 1.5 0 1 0 0 3H20v6h-6v-3.5a1.5 1.5 0 1 0-3 0V20H4v-6h3.5a1.5 1.5 0 1 0 0-3H4z"/>` |
| `globe` | NodeHub、生态、地球 | `<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 3 4 6 4 9s-1.5 6-4 9c-2.5-3-4-6-4-9s1.5-6 4-9z"/>` |
| `github` | GitHub 品牌 | `<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.4 3.4 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.4 13.4 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>` |
| `grid` | ModelZoo、格子 | `<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 3v18M16 3v18M3 8h18M3 16h18"/>` |
| `terminal` | 命令、终端 | `<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8l4 4-4 4"/><path d="M12 16h6"/>` |
| `search` | 搜索、找答案 | `<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>` |
| `list-check` | 排查清单 | `<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6l2 2 3-3M3 12l2 2 3-3M3 18l2 2 3-3"/>` |

## 语义匹配建议（讲义章节 → 图标）

| 讲义关键词 | 首选图标 |
|---|---|
| 快速开始、上手、启动 | `zap` 或 `rocket` |
| 实验、测试、验证 | `flask` |
| 讲解、学习、教学 | `gradcap` |
| 视频、直播 | `video` |
| 讲义、文档 | `book-open` |
| 代码、GitHub、示例 | `code` 或 `github` |
| 官方文档、API 手册 | `layers` |
| Camera、Audio、显示 | `film` |
| GPIO、40pin、CAN、硬件接口 | `chip` |
| ModelZoo、模型、AI | `brain` 或 `grid` |
| TROS、ROS、机器人 | `robot` |
| 系统驱动、调试 | `wrench` |
| LLM、大语言模型、对话 | `message` |
| 感知、视觉 | `eye` |
| 控制、机械臂、具身 | `arm` |
| 真实项目、精准 | `target` |
| 社区作品、优秀 | `star` |
| 拼图、组合应用 | `puzzle` |
| NodeHub、生态 | `globe` |
| 命令、终端 | `terminal` |
| 搜索、找 | `search` |
| checklist、发帖前排查 | `list-check` |

## 新增图标规范

如果讲义里出现全新语义（如"电池"、"云"），先查 Lucide 官网找对应图标，把 24×24 path 抄进本表并注明用途，再在 composer 里注册。**禁止发明 emoji 替代方案。**
