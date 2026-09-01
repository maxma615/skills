---
name: bilingual-variant
description: 从中文 slide blueprint 生成英文变体：翻译文案、切换 logo 到 logo-en、切换 URL 到英文站点、保证 slide 数与顺序完全一致。产物是英文 blueprint JSON，需由 html-slide-composer 渲染为最终 HTML。当用户已有中文 blueprint 需要英文版时使用；不用于自然语言翻译服务，也不处理其他语种。
---

# 中英双语版本生成

## 目标与边界

- 完成：把一份 `lang: cn` 的 blueprint JSON 转成 `lang: en` 版本，两者 slide 数与顺序完全对齐（相同 index 是同一张 slide）。
- 不处理：其他语种（日/韩/西班牙语等）、blueprint 结构变更、HTML 生成本身。

## 触发与反触发

| 情形 | 行为 |
|---|---|
| 用户说"给中文版做英文版" | 使用本 Skill |
| 用户已有英文讲义 md | 走 handbook-parser 直接生成英文 blueprint |
| 用户要日/韩语 | 不支持，报告需要扩展 |

## 输入与前置条件

- 必需：中文 blueprint JSON 路径。
- 预检：
  1. 输入 blueprint 的 `meta.lang == "cn"`；
  2. 每张 slide 的字段完整（不接受空字段）；
  3. `references/i18n-glossary.md` 可读。

## 产物与完成标准

- 产物：`<name>-en.json` 英文 blueprint 文件。
- 完成：
  1. `meta.lang == "en"`
  2. `meta.logo_key == "logo-en"`
  3. slide 数 == 中文版
  4. 每张 slide 的 pattern 与中文版对应位置一致
  5. 关键 URL 已切换到 `/en` 路径（`developer.d-robotics.cc/en`、`rdk_doc_center/en`、`forum-en.d-robotics.cc`）

## 执行流程

1. **加载中文 blueprint**。
2. **加载 i18n-glossary.md**，构建术语表。
3. **元信息切换**：
   - `meta.lang: cn → en`
   - `meta.logo_key: logo-cn → logo-en`
   - `meta.title` 翻译（例如"RDK 小课堂｜第一课" → "RDK Course | Lesson 01"）
4. **遍历 slides，每张按字段翻译**：
   - `kicker`：中文 kicker 直接从术语表映射（大部分 kicker 中英都是英文，不用改）
   - `title`：查术语表 + 术语外的普通中文短句译为英文；产品名保留（RDK/BPU/TROS/NodeHub/ModelZoo）
   - `lead`：整段翻译，保持"简洁、平实、去 filler"的英文调性
   - `cards[].title` / `cards[].body`：逐条翻译
   - `steps[].badge` / `steps[].body`：翻译；Step 1/2/3 保留
   - `items[]`：逐条翻译
   - `resources[].name` / `.desc` / `.href`：`name` 翻译；`href` 若是 `d-robotics.cc/xxx` 切换为 `d-robotics.cc/xxx/en`
   - `code`（命令行块）：**不翻译**，逐字保留
5. **保留 icon / tint / pattern 完全一致**（跨语言视觉锚不变）。
6. **写英文 blueprint**。

## 翻译规则

- **保留原样**：产品/品牌名（RDK、BPU、TROS、NodeHub、ModelZoo、RDK Studio、D-Robotics、GitHub、ROS）；命令行；数字；版本号；URL。
- **调性**：Apple 官网风格，去掉冠词 filler、去掉"we"，用简洁短句。
- **句子长度**：英文往往比中文长 30%，若翻译后超出 slide 承载（比如 cover 的 lead 超过 200 字符），必须精简。
- **不做**：意译到偏离原意；添加原文没有的信息。

## 验证

- **阶段验证**：每张 slide 翻译后立即比对字段个数与中文版一致（cards[] 长度不能变、steps[] 长度不能变）。
- **最终验证**：
  1. `meta.lang == "en"` 且 `meta.logo_key == "logo-en"`
  2. slide 数完全相同
  3. 每张 slide 的 `icon` / `tint` / `pattern` 字段与中文版对应位置一致
  4. 所有 URL 已切到 `/en`
  5. 中文字符残留检查：通过 regex `[一-鿿]` 扫描整个 en blueprint（除产品名、注释字段外应为 0）
- **证据保存**：打印"cn slide N 张 vs en slide N 张，pattern 对齐率 100%，中文残留 0 处"。

## 失败处理

- **术语找不到翻译**：从 `i18n-glossary.md` 找语义最接近的；仍不确定时保留中文并 `"needs_translation": true` 标记该字段；继续翻其他。
- **翻译后长度爆表**：报告哪张 slide 的哪个字段超长（比如 lead > 260 字符），请求用户简化中文原文或接受略长的英文版。
- **中文残留 > 0**：报告残留位置，用户确认后重跑该字段翻译。
- 同一策略最多 2 次；仍失败 → 保存部分结果，标记未完成字段。

## 风险与确认

- 风险等级：`low`（只生成新文件，不覆盖中文原版）。
- 若英文 blueprint 已存在 → 提示是否覆盖。

## 按需参考

- 术语表 → `references/i18n-glossary.md`
- 英文字号 → `references/design-system.md` §4"英文版"
- 长标题处理 → 英文允许 `white-space: normal`，但要控制在 2 行内不出现孤字

## 顺跑衔接

本 Skill 输出的英文 blueprint，通常紧接着交给 `html-slide-composer` 渲染：

```
handbook-parser --> blueprint-cn.json
     ↓
html-slide-composer --lang cn --> lesson-01.html
     ↓
bilingual-variant --> blueprint-en.json
     ↓
html-slide-composer --lang en --> lesson-01-EN.html
```
