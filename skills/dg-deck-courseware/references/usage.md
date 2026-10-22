# dg-deck — JSON 规格 → 单文件离线 HTML 课件

从本 Skill 目录执行。依赖见 `requirements.txt`：`fonttools` 与 `brotli` 用于构建，`playwright` 与 `Pillow` 用于渲染。浏览器使用 `playwright install chromium`，或用 `--chrome` / 环境变量 `CHROME` 指定本机 Chrome。

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
.venv/bin/python scripts/build.py examples/lesson-2-01.zh.json -o build/2-01.html
.venv/bin/python scripts/render.py build/2-01.html -o build/png --pdf build/2-01.pdf
.venv/bin/python scripts/render_cover.py --spec examples/series-cover.zh.json -o build/cover.png --thumbs
.venv/bin/python scripts/convert_rdk_blueprint.py blueprint.zh.json -o spec.json
.venv/bin/python scripts/extract_spec.py deck.html -o spec.json
```

`examples/lesson-2-01.zh.json` 按原课件重新构建时，若捆绑子集已覆盖全部字符，输出与原文件逐字节一致。缺字时从源字体重新子集化，查找顺序见 [fonts.md](fonts.md)。

打开 HTML 后：←/→/空格翻页，N 显示备注，F 全屏，S 切到滚动版。URL 参数：`?mode=scroll`、`?print=1`、`?static=1`、`?export=1`、`?notes=1`、`#页码`。

文档：[spec.md](spec.md)（JSON 格式），[layouts.md](layouts.md)（18 种版式：10 种是原版，8 种标为「重建，非原版」，另有新增 `diagram`）。

`build/` 已被仓库 `.gitignore` 忽略。生成的课件不要放进 `examples/`，除非是在添加参考样例。

系列课第 1 页用 `series-cover` 版式（见 [layouts.md](layouts.md)）。视频平台封面用 `scripts/render_cover.py --spec <课件 spec>` 从同一页的字段渲染：输出 1920×1080 的 `<out>.png` 和 1440×1080 的 `<out>_4x3.png`（中间 4:3 裁切），`--thumbs` 另出 320/240px 小图用于检查小尺寸可读性。课件第 1 页和封面图由同一模板生成，不要手改其中任何一个。

查看器界面文字（翻页提示、上一页/下一页按钮、「本页无备注」）跟随 `meta.lang`：英文课件显示英文。
