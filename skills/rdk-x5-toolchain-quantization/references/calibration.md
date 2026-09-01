# 校准数据准备完全指南

> **何时读**：
> - 默认 nv12 路径不适用（非图像输入 / 多输入模型 / 训练时用了 letterbox）
> - 默认路径量化精度掉点严重，要切到 featuremap 兜底
> - 想搞清楚为什么校准文件必须是 `.tofile()` 而不是 `.npy`，为什么 `cal_data_type` 必须是 `float32`
>
> **来源**：
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_usage/prepare_calibration_data.rst.txt`
> - `rdk_model_zoo/samples/vision/ultralytics_yolo/conversion/mapper.py`（L174-194 采样警告；L261-275 标准前处理循环）

---

## 1. 数量与代表性

| 维度 | 建议 |
|---|---|
| **起步数量** | 20 张。Model Zoo `mapper.py` **L191** 当 `img_cnt < 20` 时打 warning：`may cause the calibration to fail` |
| **上限** | 50 张。`mapper.py` **L193** 当 `img_cnt > 50` 时打 warning：`may cost a long time to calibrate`。再多对精度提升有限，主要拖慢校准 |
| **分类模型** | 20 张通常够（每类至少 1 张代表样本） |
| **检测 / 分割** | 20-50 张，覆盖小目标 / 大目标 / 多目标场景 |
| **采样原则** | 从训练集或验证集**随机**采样；覆盖光照、目标尺度、类别分布 |

**反面例子（不要这么干）**：

- 全部用纯色图 / 不含目标的图 → 激活分布失真，量化阈值统计崩
- 全部用最简单的样本（白底单目标） → 校准 cosine 高，板端真实场景掉点
- 全部用最 hard case（密集小目标 + 遮挡） → 校准 statistics 偏向极端值，常规场景精度反而退化
- 只取 1-2 张反复复制 → 等于校准统计样本数为 1-2，量化阈值不可靠

---

## 2. nv12 默认路径（与 SKILL.md 一致）

这是 **YOLO / 分类 / 大多数 RGB 图像模型** 的默认路径。脚本输出 raw bytes，归一化交给 yaml 的 `norm_type: data_scale` + `scale_value`。

```python
# prepare_calibration.py —— 与 Model Zoo ultralytics_yolo/conversion/mapper.py 一致
import cv2, numpy as np
from pathlib import Path

SRC, OUT = Path('./cal_src'), Path('./calibration_data')
OUT.mkdir(exist_ok=True)
W, H, NUM = 640, 640, 20      # 20 起步；>50 校准会很慢

jpgs = [p for p in SRC.iterdir() if p.suffix.lower() in ('.jpg', '.png', '.jpeg')]
if len(jpgs) > NUM:
    idx = np.random.choice(len(jpgs), NUM, replace=False)   # 随机采样，避免数据顺序偏差
    jpgs = [jpgs[i] for i in idx]

for p in jpgs:
    img = cv2.imread(str(p))                       # BGR uint8 HWC
    x = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)       # → RGB（对齐 input_type_train）
    x = cv2.resize(x, (W, H))                      # 直接 resize（YOLO 训练即如此）
    x = np.transpose(x, (2, 0, 1))                 # HWC → CHW
    x = np.expand_dims(x, 0).astype(np.float32)    # NCHW float32，[0, 255] 原始像素
    x.tofile(OUT / (p.stem + '.rgbchw'))           # raw bytes，不做归一化
```

逐行对应 Model Zoo `mapper.py` **L261-275**：`cv2.imread → cvtColor BGR2RGB → resize → transpose HWC2CHW → expand_dims → astype(float32) → tofile`。

### 为什么不能用 .npy

| 落盘方式 | 文件结构 | 大小（1×3×640×640 float32） |
|---|---|---|
| `tensor.tofile(path)` | 纯数据，**N×C×H×W×4** bytes | 4 915 200 bytes |
| `np.save(path, tensor)` | **128 字节 numpy header** + 纯数据 | 4 915 328 bytes |

`hb_mapper` 在校准时用 **`np.fromfile`**（即 `numpy.fromfile`）读取（见来源 RST L18），按 `cal_data_type` 指定的 dtype 直接解释整个文件，**不会识别也不会跳过 npy header**——它不是用 `np.load`，所以根本没有 header 解析逻辑。

后果：

- 头部 128 字节被当成 tensor 的前 32 个 float32 值塞进网络第一层；
- 这 32 个值大约对应 numpy magic number + dict 字面量编码，数值范围跟图像像素完全不一致；
- 校准 statistics（min / max / KL 分布）严重偏移；
- 量化阈值整体走偏，cosine 经常掉到 < 0.9，且 `hb_mapper` 不会报错。

**结论**：必须用 `tensor.tofile(path)`。文件后缀（`.rgbchw` / `.bin` / `.bgr`）只是惯例，工具链不识别后缀。

### 验证 bin 文件大小

每张校准样本的字节数必须严格等于 `N × C × H × W × sizeof(float32)`：

```bash
ls -l calibration_data/*.rgbchw | head -3
# 期望每个文件 4915200 字节（1*3*640*640*4）

python -c "print(1*3*640*640*4)"
# 4915200
```

若大小不符：

- 多出 128 字节 → 误用 `np.save`，改用 `tofile`
- 大小是 1/4 → `astype(np.float32)` 漏了，写成 uint8 了，但 yaml 写的是 float32 → 长度对不上
- 大小是 3 倍 → `expand_dims` 漏了，写成 N=3 而非 N=1

---

## 3. 多种输入类型的校准 bin 内容

> 部分内容与 yaml-reference.md 重合；这里只讲 **校准 bin 文件里装什么** 的视角。具体 yaml 字段写法见 `yaml-reference.md`。

### nv12 / rgb / bgr / yuv444（部署路径）

- 校准 bin 内容：`uint8 → float32` 的 **[0, 255] raw 像素**，已经 resize 和 channel 对齐，**未归一化**
- yaml：`norm_type: data_scale` + `scale_value: 0.003921568627451`（即 1/255），让 `hb_mapper` 在模型前面插一个归一化算子
- 优点：板端运行时 `hbDNN` 接收原始 nv12 / rgb 图像，归一化算子被 BPU 吸收，部署最简单
- 适用：YOLO、分类、大多数 RGB / 单通道图像模型

### featuremap（板外预处理路径）

- 校准 bin 内容：**已经归一化的 float32 tensor**（mean、std 都在脚本里做完）
- yaml：`norm_type: no_preprocess`，工具链不再插归一化算子
- 适用场景：
  1. **精度兜底**：默认 nv12 路径量化后 cosine 不达标，切 featuremap 把归一化挪到板外（精度调优方法详见 `accuracy-tuning.md`）
  2. **非图像输入**：点云、特征向量、音频频谱等不是 uint8 像素的输入
  3. **多输入模型**：其中一路是 feature embedding 时通常走 featuremap
  4. **复杂前处理**：训练时用了非标准 mean/std、自定义归一化（如 ImageNet (0.485, 0.456, 0.406) / (0.229, 0.224, 0.225) 三通道独立 std），且不方便用 yaml 表达时

featuremap 校准脚本（与 nv12 脚本的关键差异：**多一行 `/255.0` 归一化**，落盘后缀改 `.bin`）：

```python
# prepare_calibration_featuremap.py —— featuremap 路径
# 注意：输出目录与 nv12 路径不同（避免 yaml 切换时校准 bin 互相覆盖）
import cv2, numpy as np
from pathlib import Path

SRC, OUT = Path('./cal_src'), Path('./calib_data_featuremap')   # ← 不同于 nv12 的 ./calibration_data
OUT.mkdir(exist_ok=True)
W, H, NUM = 640, 640, 20

# 训练用 ImageNet mean/std 时打开下面两行；YOLO 等只做 /255 的训练保持注释
# MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
# STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)

jpgs = [p for p in SRC.iterdir() if p.suffix.lower() in ('.jpg', '.png', '.jpeg')]
if len(jpgs) > NUM:
    idx = np.random.choice(len(jpgs), NUM, replace=False)
    jpgs = [jpgs[i] for i in idx]

for p in jpgs:
    img = cv2.imread(str(p))
    x = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x = cv2.resize(x, (W, H))
    x = np.transpose(x, (2, 0, 1)).astype(np.float32)
    x = x / 255.0                                  # ← featuremap：必须自己做归一化
    # x = (x - MEAN) / STD                         # ← 训练用 ImageNet mean/std 时取消注释
    x = np.expand_dims(x, 0)
    x.tofile(OUT / (p.stem + '.bin'))              # 后缀习惯用 .bin
```

切到 featuremap 后，yaml 的 `cal_data_dir` 要同步改成 `./calib_data_featuremap`（不要让两条路径共用 `./calibration_data` 目录，否则会互相覆盖）。

---

## 4. 多输入模型

当 ONNX 有多个输入节点时，校准目录用子文件夹分离：

```
calibration_data/
├── input_0/                  # 对应 ONNX 第 1 个输入
│   ├── 0001.bin
│   ├── 0002.bin
│   └── ...
└── input_1/                  # 对应 ONNX 第 2 个输入
    ├── 0001.bin
    ├── 0002.bin
    └── ...
```

- yaml 的 `cal_data_dir` 指向**父目录** `./calibration_data`
- `hb_mapper` 按 ONNX 输入节点的**顺序**匹配子目录（按字典序），子目录名本身不重要，但建议用 `input_0 / input_1` 这种顺序可读名
- 同一索引（如 `0001.bin`）的多路样本必须语义对齐——一组校准样本要么一起算训练集第 i 个 batch，要么一起算同一帧的多模态输入
- 多输入模型的 `input_type_rt` / `input_type_train` / `norm_type` / `scale_value` 在 yaml 里也要按输入顺序用分号 `;` 拼接

---

## 5. letterbox（保持宽高比）

**默认不用 letterbox**——Model Zoo 的 YOLO11 / YOLOv5 等转换脚本（`mapper.py` L271）都是 `cv2.resize(x, (W, H))` 直接拉伸。

**判断准则**：

> **训练时怎么 resize 的，校准时就怎么 resize。**

- 训练用 ultralytics 原生 dataloader 的 `imgsz=640` + 默认 letterbox=True → 校准也应该用 letterbox
- 训练直接 `cv2.resize` 拉伸 → 校准就 `cv2.resize`
- 不一致的后果：检测框位置偏移、分类区域错位、cosine 看着 OK 但板端 mAP / Top-1 异常

如训练用了 letterbox（YOLO 系列大多如此），校准脚本里把 `cv2.resize(x, (W, H))` 替换为：

```python
def letterbox(img, new_h, new_w, pad_val=114):
    """
    保持宽高比 resize，剩余区域填充 pad_val（YOLO 惯例 114）。
    img: HWC uint8（BGR 或 RGB 都可，函数对通道无要求）
    return: new_h x new_w x C，dtype 与输入一致
    """
    h, w = img.shape[:2]
    r = min(new_h / h, new_w / w)              # 缩放比，取小的保证完整放进画布
    nh, nw = int(round(h * r)), int(round(w * r))
    img_r = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)

    # 计算上下左右 padding（居中放置）
    top = (new_h - nh) // 2
    bottom = new_h - nh - top
    left = (new_w - nw) // 2
    right = new_w - nw - left

    out = cv2.copyMakeBorder(
        img_r, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=(pad_val, pad_val, pad_val)
    )
    return out

# 调用：x = letterbox(x, H, W)
```

---

## 6. 常见预处理陷阱

| 错误 | 现象 | 修复 |
|---|---|---|
| 漏掉 BGR→RGB（或多做一次） | 量化 cosine ~0.6，板端检测框颜色类别预测错 | 检查 yaml `input_type_train` 与脚本 `cvtColor` 一致：`input_type_train: rgb` ↔ `BGR2RGB` |
| 用 `.npy` 不是 `.tofile()` | `hb_mapper` 不报错，cosine < 0.9，定位困难 | 改用 `tensor.tofile(path)`，参见 §2 |
| 校准张数 < 20 | `mapper.py` L191 warning：`may cause calibration to fail`；统计样本不足 | 增加到 20+ 张，从训练集随机采样 |
| 校准张数 > 50 | `mapper.py` L193 warning；校准耗时数十分钟到小时级 | 控制在 20-50 张，再多收益边际递减 |
| letterbox 与训练不一致 | 浮点 ONNX cosine 看着 OK，板端检测框位置整体偏移 | 对齐训练时 resize 方式：训练 letterbox → 校准 letterbox |
| nv12 路径手动除 255 | 双重归一化（脚本除一次，yaml `data_scale` 再除一次） | nv12 路径下校准 bin **不做归一化**，归一化由 yaml `norm_type: data_scale` 完成 |
| featuremap 路径忘了归一化 | nv12 yaml 默认 `data_scale` 没改，但脚本输出已归一化 → 数据被再除一次 255 | featuremap 路径 yaml 必须 `norm_type: no_preprocess` |
| `cal_data_type` 与脚本 dtype 不一致 | 文件大小对得上但数值被错位解释 | yaml `cal_data_type: float32` 必须与脚本 `astype(np.float32)` 一致 |
| `expand_dims` 漏写 | 文件大小是预期的 1/N | 加 `np.expand_dims(x, 0)` 把 CHW → NCHW |
| 校准目录混了非图像文件 | `mapper.py` L179 warning 后跳过；若混入 `.txt` 标签反而被 `hb_mapper` 当样本读 | 校准目录只放校准 bin 文件，标签、README 都不要放 |
| 多输入模型子目录顺序错 | 输入串位，cosine 极低 | 子目录按字典序对应 ONNX 输入顺序，建议命名 `input_0 / input_1` |

---

更多上下游话题：

- yaml 字段（`norm_type` / `scale_value` / `cal_data_type` / `cal_data_dir` 等）的完整字段列表 → `references/yaml-reference.md`
- 校准做好但量化精度仍不达标（cosine < 0.95）→ `references/accuracy-tuning.md`
- `hb_mapper makertbin` 阶段报错 / 校准日志读不懂 → `references/troubleshooting.md`
