# 中英对照术语表

> 生成英文版 blueprint 时使用。**产品名保持原样**（RDK / BPU / TROS / NodeHub / ModelZoo 都是英文品牌名，中英通用不翻译）。

## 一、导航与结构类

| 中文 | 英文 |
|---|---|
| 导学 | Course Guide |
| 第一课 / Lesson 01 | Lesson 01 |
| 本课 | this lesson |
| 下一课 | Next lesson / Up next |
| 附录 | Appendix |
| 小结 | Summary |
| 拓展练习 | Exercises |
| 常见问题 | FAQ / Common Issues |
| 学习路径 | Learning path |
| 推荐学习方式 | How to learn |

## 二、Kicker 常用短语

kicker 是 slide 顶部小写橙色标签，中英文页面**都用英文**。

| 讲义章节意图 | Kicker（英文，用于两语版本）|
|---|---|
| 封面 | Lesson 01 · RDK Course |
| 课程目标 | Course Goal / What This Solves |
| 完成后能做到 | What You'll Learn |
| 开始前确认 | Before You Start |
| 资源地图 | Resource Map |
| 关键概念 | Key Concepts |
| 官方文档 | Documentation |
| NodeHub | NodeHub |
| GitHub / ModelZoo | Source & Models |
| 论坛提问 | Community |
| 发帖三件事 | Before You Post |
| 基础排查四步 | Baseline Debug |
| 提问模板 | Question Template |
| 本课完成标准 | Completion Checklist |
| 常见问题 | FAQ |
| 本课小结 | Summary |
| 拓展练习 | Exercises |
| 下一课预告 | Up Next |

## 三、RDK 生态术语

| 中文 | 英文 |
|---|---|
| 板卡 | board（不要用 dev board 太长）|
| 上手 / 快速上手 | Get started / bring-up |
| 烧录 | Flashing (image) |
| 启动 | Boot / boot-up |
| 系统镜像 | System image |
| 外设 | Peripherals |
| 远程连接 | Remote access |
| 视频编解码 | Video codec |
| 具身智能 | Embodied AI |
| 感知与理解 | Perception |
| 控制与交互 | Control & interaction |
| 模型部署 | Model deployment |
| 模型量化 | Model quantization |
| 板端推理 | On-device inference |
| 精度验证 | Accuracy validation |
| 工具链 | Toolchain |
| 开发者社区 | Developer community |
| 官方文档 | Official docs / Documentation |
| 讲解视频 | Video / Video walkthrough |
| 配套讲义 | Handbook |
| 官方 Demo | Official demo |
| 分支 | Branch |
| 引导程序 | Bootloader (`miniboot`) |
| 二次开发 | Extension / customization |
| 节点 | Node |
| 话题 | Topic |
| 功能包 | Package |
| 硬件接口 | Hardware I/O |
| 系统驱动 | System & drivers |
| 底层调试 | Low-level debugging |

## 四、常见句式翻译

| 中文表述 | 英文表述 |
|---|---|
| 从零基础开始 | For beginners / from scratch |
| 第一次接触 RDK | First-time RDK users |
| 快速完成上手 | Get up and running quickly |
| 建立资源地图 | Build a resource map |
| 每一步都会更顺畅 | Everything after that goes smoother |
| 先建立 X 再开始 Y | Build X first, then Y |
| 报错后不知道去哪找答案 | You hit an error, but you don't know where to look |
| 会找答案本身就是一种能力 | Knowing where to look is a skill of its own |

## 五、发帖相关

| 中文 | 英文 |
|---|---|
| 论坛 | Forum |
| 发帖前先做三件事 | Do three things before you post |
| 搜论坛关键词 | Search the forum |
| 查官方文档 | Check the official docs |
| 查 GitHub Issues | Search GitHub Issues |
| 基础排查 | Baseline debug |
| 查版本 | Check version |
| 升级软件包 | Update packages |
| 升级 miniboot | Update miniboot |
| 跑官方 Demo | Run the official demo |
| 复现步骤 | Steps to reproduce |
| 预期结果 | Expected result |
| 实际结果 | Actual result |
| 复现概率 | Reproduction rate |
| 已做排查 | What I've already checked |
| 关键日志 | Key logs |

## 六、语气与调性

- 中文原文常用"务必""建议""请"等祈使 → 英文用平实的 "make sure to..." 或 "recommend..."，避免命令感。
- 中文用"我们"（"我们从第一课开始"）→ 英文可用"We start with Lesson 01" 或去掉主语 "Lesson 01 starts with..."。
- 中文用"这是"（"这是入门篇"）→ 英文 "Here's..." 或直接 "Basics: ..."。
- 中文 slide 的口播感强 → 英文尽量简洁，减掉冠词和 filler words。

## 七、图标语义无需翻译

`icon` 字段永远用 key（`brain`/`robot`/`chip`...），中英 blueprint 都一样。图标本身跨语言。

## 八、logo 与 URL 切换

| 中文 blueprint | 英文 blueprint |
|---|---|
| `"logo_key": "logo-cn"` | `"logo_key": "logo-en"` |
| `href: "https://developer.d-robotics.cc/"` | `href: "https://developer.d-robotics.cc/en"` |
| `href: "https://developer.d-robotics.cc/rdk_doc_center/"` | `href: "https://developer.d-robotics.cc/rdk_doc_center/en"` |
| `href: "https://forum.d-robotics.cc/"` | `href: "https://forum-en.d-robotics.cc/"` |
| `href: "#"` (飞书讲义) | `href: "#"` （目前留空，未来 EN 讲义单独维护）|
