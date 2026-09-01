# 精度调优手册

> **何时读**：cosine 不达标（参考 `accuracy.md` 中的阈值定义）/ 板端推理结果与浮点 ONNX 差异肉眼可见 / 想用 `accuracy_debug` (`hmct-debugger`) 定位敏感算子 / 已尝试常规调优仍不达标，需要切 featuremap 兜底排查 RGB↔YUV 与归一化误差源。
>
> **来源**：
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/tune_content/accuracy_tune.rst.txt`（PTQ 模型精度调优总章）
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_tool/accuracy_debug.rst.txt`（精度 debug 工具 `hmct-debugger`）
>
> 本文只覆盖**调优策略与决策**。yaml 字段全集见 `yaml-reference.md`；校准数据准备见 `calibration.md`；精度度量阈值与测量方法见 `accuracy.md`；环境与 OE 安装见 `setup.md`；运行时 / 编译报错见 `troubleshooting.md`。

---

## 0. 调优决策树

按顺序从上到下尝试，每一步都要重新走 `accuracy.md` 的度量流程确认是否到位，未达标再进下一档。**前一步不要跳过**——跳到第 4、5 步的开销远大于第 1~3 步。

```
cosine < 阈值（参考 accuracy.md：分类 ≥0.99 / 检测 ≥0.95 / 分割 ≥0.95）
    │
    ├── 1. 检查校准数据
    │     · 数量是否够（20 张起步，>50 校准耗时显著上升；大规模分类如 ImageNet 可加到 100+）
    │     · 是否覆盖典型分布 / 各类别 / 各分支
    │     · 预处理是否与训练对齐（resize 插值、归一化、通道序）
    │     · 文件格式（.rgb/.bgr/.yuv，不是 .npy）
    │     · shape 与 yaml input_shape 一致
    │
    ├── 2. 切换 calibration_type
    │     default  → 自动搜索（默认）
    │     mix      → 多策略混合，敏感模型首选
    │     kl       → 长尾分布友好
    │     max      → 配合 max_percentile 调分位数
    │     load     → 复用已保存的量化参数
    │     可叠加：per_channel / asymmetric / bias_correction
    │
    ├── 3. accuracy_debug 定位敏感算子
    │     hmct-debugger get-sensitivity-of-nodes
    │     找 cosine 最低的 1~2 个节点 → 写入 yaml node_info：
    │       · CPU 回退（'ON': 'CPU'，仅尾部 1~2 个算子）
    │       · 或 'ON': 'BPU' + int16（留在 BPU 但用 16bit）
    │
    ├── 4. 主导算子批量 int16（整体精度优先）
    │     calibration_parameters.optimization:
    │       set_Conv_input_int16,set_Conv_output_int16,
    │       set_Mul_input_int16,set_Mul_output_int16, ...
    │     代价：bin 体积 ~2x，推理 30~50% 慢；仅在第 3 步还不够时启用
    │
    └── 5. 切 featuremap 兜底
          input_type_rt: 'featuremap' + norm_type: 'no_preprocess'
          校准数据改用 float32 .bin（预处理在外部完成）
          诊断价值：featuremap 好但 nv12 差 → 锅在 RGB/YUV 或归一化
                    两者都差 → 锅在模型 / 校准数据本身
```

如果走完这 5 步精度仍不达标，最后兜底是 QAT（量化感知训练），需要从训练框架重新介入；这超出 PTQ 工具链范围，不在本手册讨论。

**特例 — Deformable Attention decoder cosine < 0（符号翻转）**：
若 `quant_info.json` 中 decoder 节点（尤其 `cross_attn/Sub`、`Transpose`、`Split`）的 cosine_similarity 为**负值**，上述 5 步全部无效——这是 INT8 scale 估算在负值域出错导致的符号翻转，不是校准参数问题。**直接跳过调优流程**，参考 `troubleshooting.md §10` 的可行路径（升级 OE / QAT / 换模型）。

---

## 1. 校准数据自检清单

每次调优**先**核对这 5 项；80% 的精度问题在这一步就能排掉，不必再动 yaml。详细要求和准备脚本见 `calibration.md`。

1. **数量**：20 张起步（Model Zoo `mapper.py` L191 在 `<20` 时打 warning）；20-50 张是常见甜区，超过 50 张校准耗时显著上升；大规模分类（如 ImageNet 1000 类）可酌情加到 100+，但 RST 推荐区间是 20-100。详细见 `calibration.md` §1。
2. **代表性**：覆盖训练集典型分布，多任务 / 多分类时**每个分支 / 类别都要有样本**。避免过曝、纯黑纯白、无目标背景等异常数据。
3. **预处理与训练对齐**：`resize` 插值方式（默认 `cv2.INTER_LINEAR`）、`mean / scale` 值、通道序（BGR vs RGB）必须与训练阶段完全一致。`skimage.imread` 返回 RGB / float / 0~1，`cv2.imread` 返回 BGR / uint8 / 0~255，两者**不能混用**。
4. **存储格式**：用 `.rgb` / `.bgr` / `.yuv` 等裸数据，**不要用 `.npy`**。`np.tofile` 不保存 shape 和 dtype，加载端必须知道。
5. **shape 一致**：`(C, H, W)` 或 `(N, C, H, W)` 与 yaml `input_shape` 字面对齐，否则校准会静默跑错。

**重要交叉验证**：跑完 `hb_mapper makertbin` 后，用 `*_original_float_model.onnx` 跑一遍验证集，精度应与原始浮点 ONNX **小数点后 3~5 位**对齐。如果这一步就不对齐，问题在数据处理（pipeline / 预处理 / read_mode），不要急着调 calibration_type。

---

## 2. calibration_type 切换

`default` 是自动搜索，会从 `max` / `max-percentile 0.99995` / `kl` 中选一个并尝试叠加 `per_channel` / `asymmetric`，转换日志会打印类似 `Select kl method.` / `Perchannel quantization is enabled` / `Asymmetric quantization is enabled` 的字样。如果 `default` 仍不达标，按下表手动切换：

| 类型 | 何时尝试 | 副作用 / 备注 |
|---|---|---|
| `default` | 默认起点，自动搜索 | 通常已经覆盖 80%+ 场景 |
| `mix` | `default` 后精度仍差 1.5%~3%，**首选**手动尝试 | 多策略混合，转换耗时略增 |
| `kl` | 激活分布长尾、`mix` 也不够 | 对极端值不敏感，但对均匀分布偏保守 |
| `max` | 激活分布相对均匀，需要逼近真实最大值 | 必须配合 `max_percentile` 调分位数；推荐顺序 `0.99999 → 0.99995 → 0.9999 → 0.9995 → 0.999`，观察趋势找最佳值 |
| `load` | 已经标定过、想复用 scale / threshold | 只在已有可信量化参数时使用 |

可叠加的 `optimization` 子项：

- `per_channel`：在以上策略中选 cosine 最高方案后再开启，常能再涨 0.5%~1%。
- `asymmetric`：非对称量化，针对激活不以 0 为中心的场景。
- `bias_correction`：补偿量化引入的偏置漂移，部分场景有效。

字段语义与位置详见 `yaml-reference.md` 的 `calibration_parameters` 章节，本文不重复字段说明。

---

## 3. accuracy_debug 定位敏感算子 + node_info 修复

精度损失的根因通常是两类：**敏感节点量化误差**（个别算子用 int8 后 cosine 骤降）和**节点误差累积**（每层一点点损失，汇总到输出已经偏大）。`hmct-debugger` 工具就是用来区分并定位这两类问题的。

### 3.1 开启 dump_calibration_data

在 yaml `model_parameters` 中加：

```yaml
model_parameters:
  debug_mode: "dump_calibration_data"
```

重新跑 `hb_mapper makertbin`，会额外产出：

- `calibrated_model.onnx`：含 `HzCalibration` 校准节点的中间模型（任何时候都会产出）。
- `calibration_data/`：经过颜色空间转换和预处理后的 `.npy` 校准数据，目录结构：
  ```
  calibration_data/
  ├── input.1/         # 文件夹名 = 模型输入节点名
  │   ├── 0.npy
  │   ├── 1.npy
  │   └── ...
  └── input.2/         # 多输入模型会有多个文件夹
      └── ...
  ```

> 注意：这里的 `.npy` 与 `calibration.md` §2 `prepare_calibration.py` 产出的裸 RGB/BGR 数据**不同**——这里是经过工具链颜色空间转换（BGR→YUV444 / GRAY 等）和预处理后的最终输入张量，可直接 `np.load()` 喂模型。

### 3.2 命令行：节点敏感度排序

定位 cosine 最低的算子，最常用：

```bash
hmct-debugger get-sensitivity-of-nodes \
    calibrated_model.onnx \
    calibration_data \
    -m "['cosine-similarity','mse']" \
    -n node \
    -v True
```

关键参数（完整列表 `hmct-debugger get-sensitivity-of-nodes -h`）：

| 参数 | 缩写 | 含义 |
|---|---|---|
| `model_or_file` | 固定 | 校准模型 `.onnx` 路径，必填 |
| `calibrated_data` | 固定 | 校准数据目录，必填 |
| `metrics` | `-m` | 度量方式：`cosine-similarity` / `mse` / `mre` / `sqnr` / `chebyshev`，可多选，结果按首项排序 |
| `node_type` | `-n` | `node`（普通节点） / `weight`（权重校准节点） / `activation`（激活校准节点） |
| `output_node` | `-o` | 指定中间节点为输出来计算敏感度；默认 None = 用模型最终输出 |
| `data_num` | `-d` | 参与计算的样本数；默认 1，最大 = `calibration_data` 总数 |
| `verbose` | `-v` | `True` 时打印到终端（按首个 metric 排序） |
| `interested_nodes` | `-i` | 只算指定节点，优先级高于 `node_type` |

等价 Python API：

```python
import horizon_nn.quantizer.debugger as dbg
import logging
logging.getLogger().setLevel(logging.INFO)

node_message = dbg.get_sensitivity_of_nodes(
    model_or_file='./calibrated_model.onnx',
    metrics=['cosine-similarity', 'mse'],
    calibrated_data='./calibration_data/',
    output_node=None,
    node_type='node',
    data_num=None,
    verbose=True,
    interested_nodes=None,
)
```

### 3.3 读输出找敏感算子

`verbose=True` 终端输出（按 cosine 升序排，**越靠前 = 量化引入误差越大**）：

```
=================node sensitivity=================
node                  cosine-similarity  mse
---------------------------------------------------
Conv_60               0.77795            68.02103
Conv_48               0.78428            64.36318
Conv_82               0.80394            61.09268
Conv_94               0.80499            65.05224
Conv_42               0.83787            49.4949
...
Conv_31               0.91637            28.79291
```

读法：

- 排第 1 的 `Conv_60` 是**最敏感**的节点——单独量化它会让模型输出 cosine 掉到 0.778。
- 关注头部 1~2 个明显低于其他节点的算子（这里 `Conv_60` / `Conv_48` 显著低于第 7 名 `Conv_54` 的 0.866）。
- 也可换 `-n activation` 看激活校准节点；输出会多两列 `threshold` 和 `bit`（量化比特），其中 `bit=16` 表示该节点已经在 int16 计算。
- 累积误差曲线（`hmct-debugger plot-acc-error`）适合分析"误差累积型"问题，关注**靠近模型输出**的曲线段——选累积误差小的方案优先。

### 3.4 把敏感算子写入 yaml `node_info`

定位到敏感算子（假设是 `Conv_60` 和 `Conv_48`）后，在 yaml 中通过 `node_info` 指定它们的量化策略。两种处理：

**A. 回退 CPU 高精度（`'ON': 'CPU'`）**：算子整段在 CPU 上以 float 计算，精度最高但有性能代价。**仅适合模型尾部 1~2 个算子**——中间节点回退到 CPU 会反复量化 / 反量化，反而引入更大误差，且 CPU 节点会打断 BPU 子图导致整体性能下滑。这是官方文档（`hb_mapper_makertbin.rst`）描述的 "CPU 回退" 机制，无需其他开关字段。

```yaml
model_parameters:
  # ... 其他字段见 yaml-reference.md
  node_info: {
    "Conv_60": {
      'ON': 'CPU'
    },
    # 也可以同时挂第二个尾部算子
    "Conv_94": {
      'ON': 'CPU'
    }
  }
```

**B. 留在 BPU 但提升到 int16**：算子继续在 BPU 上跑，比特位从 int8 提到 int16。精度提升相对于 CPU 回退略小，但**不会破坏 BPU 子图连续性**，性能代价远小于回退 CPU，是中间敏感节点的首选。

```yaml
model_parameters:
  node_info: {
    "Conv_60": {
      'ON': 'BPU',
      'InputType': 'int16',
      'OutputType': 'int16'
    }
  }
```

> 短形式也合法（只配数据类型时）：`node_info: 'Conv_60:int16;Conv_94:int16'`。完整字段语义见 `yaml-reference.md`。

### 3.5 实操工作流（5 步循环）

```
  1. yaml 加 debug_mode: "dump_calibration_data" 重跑一次 hb_mapper makertbin
     ├── 产出 calibrated_model.onnx + calibration_data/
  2. hmct-debugger get-sensitivity-of-nodes 取节点敏感度排序
     ├── 锁定 cosine 最低的 1~2 个节点
  3. 在 yaml node_info 给它们加 `'ON': 'CPU'`（尾部回退）或 `'ON': 'BPU' + int16`（中间）
  4. 重跑 hb_mapper makertbin（可去掉 debug_mode 节省时间）→ 跑 accuracy.md 度量
  5. 若仍不达标 → 把下一个敏感节点加进去，回到第 3 步；
                  否则收工
```

> 经验值：尾部 CPU 回退**不要超过 2 个算子**，否则性能下滑通常 >30%；中间 int16 节点**累计不要超过 5~10 个**，否则不如直接走第 4 步全模型 int16。

---

## 4. 主导算子批量 int16（整体精度优先）

第 3 步逐个节点调优后仍不够时，把模型主导算子类型一次性提到 int16。OE 1.2.8 没有"一键全模型 int16"开关——通过 `optimization` 字段按 ONNX **算子类型**（NodeKind）批量声明：

```yaml
calibration_parameters:
  calibration_type: 'default'  # 或前面调好的最佳类型
  optimization: 'set_Conv_input_int16,set_Conv_output_int16,set_Mul_input_int16,set_Mul_output_int16,set_Add_input_int16,set_Add_output_int16'
```

**`{NodeKind}`** 是 ONNX 算子类型字符串（如 `Conv` / `Mul` / `Add` / `Sigmoid` / `Gemm` / `MatMul` / `Softmax`）。建议覆盖：

- 卷积型：`Conv` / `Gemm` / `MatMul`
- 逐元素型：`Mul` / `Add` / `Sub`
- 激活型：`Sigmoid` / `HardSigmoid` / `Tanh`
- 归一化 / Pool（按需）

> **检查清单**：跑 `hb_mapper checker` 输出的 BPU 算子表，把里面 frequency 高的算子 type 都加进 `optimization`。漏掉的类型仍是 int8，可能局部精度不达标。如果想"覆盖所有算子"，最直接的办法是改用 `node_info` 把每个节点显式标 int16（或参考 yaml-reference.md §6 的写法）。

**代价**：

- 编译产物 `.bin` / `.hbm` 体积约 **2 倍**（权重存储位宽翻倍）。
- 推理耗时通常增加 **30%~50%**，BPU 利用率下降。
- 板端内存占用同步上升。

**适用场景**：

- 模型对量化整体敏感（敏感节点超过 10 个）。
- 精度优先级**高于**性能 / 体积（如医疗、安防关键链路）。
- 第 3 步逐节点 int16 已经接近这个数量级，性能代价相当，不如一次到位。

启用后通常不再需要 CPU 回退（`'ON': 'CPU'`）——若已经把主导算子全标 int16 还有零星敏感算子未达标，那些算子很可能是模型结构问题（如自定义 op、动态 shape 分支），考虑改模型或上 QAT。

---

## 5. featuremap 精度兜底

### 5.1 触发条件

当**同时满足**以下条件时启用：

- 模型走 `nv12` / `yuv444` 输入路径，cosine 显著偏低（比浮点 ONNX 差 >3%）。
- 已经尝试 `calibration_type` 切换（§2）和 CPU 回退（`'ON': 'CPU'`）/ int16 节点调优（§3），仍不达标。
- 怀疑误差来自：RGB↔YUV 颜色空间转换、工具链插入的归一化节点、`mean_value` / `scale_value` 与训练时不一致。

featuremap 路径让用户**在外部完成所有预处理**（颜色空间、归一化、数值范围），工具链拿到的是已经规整好的 float32 张量，跳过所有易错的 BGR→YUV 与 mean/scale 插入逻辑。

### 5.2 yaml 改动（block diff 风格）

把 `input_parameters` 改成 featuremap 形式：

```yaml
input_parameters:
  input_name: ''                       # 留空 = 用 onnx 默认输入名
  input_type_rt: 'featuremap'          # 关键：板端运行时输入类型
  input_type_train: 'featuremap'       # 关键：训练时的输入类型
  input_layout_train: 'NCHW'           # 与模型实际一致
  input_shape: '1x3x640x640'           # 与模型实际一致
  norm_type: 'no_preprocess'           # 关键：不让工具链插归一化节点
  # ↓↓↓ 删除这些字段（如果原来有的话） ↓↓↓
  # mean_value: '0.0 0.0 0.0'
  # scale_value: '0.003921568627 0.003921568627 0.003921568627'
```

### 5.3 校准数据脚本（与 `calibration.md` 的 nv12 脚本不同）

featuremap 路径要求每张校准图被**完整预处理**到 float32 张量（归一化、通道序、layout 全部到位），然后保存为 `.bin`：

```python
#!/usr/bin/env python3
# prepare_featuremap_calib.py
# 与 calibration.md 的 nv12 脚本相对：那个脚本只做颜色空间转换，
# 这个脚本要把图片处理成模型直接可用的 float32 张量。

import os
import cv2
import numpy as np
from pathlib import Path

SRC_DIR  = Path('./calib_images')        # 原始 jpg/png 校准图
DST_DIR  = Path('./calib_data_featuremap')  # 输出 .bin
INPUT_H  = 640
INPUT_W  = 640
# 训练时用的是 BGR 还是 RGB？必须与训练一致，错一个就白调
USE_RGB  = True

DST_DIR.mkdir(parents=True, exist_ok=True)

for idx, img_path in enumerate(sorted(SRC_DIR.glob('*'))):
    if img_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.bmp'}:
        continue

    img = cv2.imread(str(img_path))                # BGR, uint8, 0~255
    if img is None:
        print(f'[skip] cannot read {img_path}')
        continue

    if USE_RGB:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # resize 到模型输入尺寸（插值方式必须与训练一致）
    img = cv2.resize(img, (INPUT_W, INPUT_H), interpolation=cv2.INTER_LINEAR)

    # 归一化：[0,255] uint8 → [0,1] float32（即除以/255，与训练保持一致）
    # 如果训练用的是 ImageNet mean/std，要在这里加：
    #     x = (x - mean) / std
    x = img.astype(np.float32) / 255.0

    # HWC → CHW，layout 必须与 yaml input_layout_train 一致
    x = np.transpose(x, (2, 0, 1))                 # CHW
    x = np.ascontiguousarray(x, dtype=np.float32)

    # 保存为裸 .bin（不要存 .npy，工具链不读 .npy 头）
    out_path = DST_DIR / f'{idx:04d}.bin'
    x.tofile(str(out_path))

print(f'done: {len(list(DST_DIR.glob("*.bin")))} files in {DST_DIR}')
```

对应 yaml 中 `calibration_parameters.cal_data_dir` 指向 `./calib_data_featuremap`，`cal_data_type` 设为 `float32`（字段语义见 `yaml-reference.md`）。

### 5.4 诊断价值

featuremap 路径的真正作用不只是"调高精度"，更是**二分定位**误差来源：

| 现象 | 结论 |
|---|---|
| nv12 路径 cosine 低，featuremap 路径 cosine 正常 | 锅在 RGB↔YUV 转换 或 工具链插入的 mean/scale 节点 → 回头检查 `input_type_rt` / `input_type_train` 配对、`mean_value` / `scale_value` 与训练对齐 |
| nv12 与 featuremap 都低 | 锅在模型本身（含敏感算子）或校准数据 → 回到 §3 走 `accuracy_debug`，或回 §1 检查校准数据 |
| nv12 低，featuremap 中等（仍未达标） | 部分锅在颜色空间转换，但模型本身也有量化压力 → §3 + featuremap 同时上 |

**部署侧代价**：featuremap 把预处理责任推回应用层——板端不能直接喂 nv12 摄像头流，必须先在 CPU/GPU 做颜色转换 + 归一化。对实时性敏感的链路，确认完根因后**优先回 nv12 路径**修真因，featuremap 只作为诊断和最后兜底，不建议长期跑生产。

---

## 6. 调优案例：典型修复路径（示例）

以下为**示例**，用于展示决策树的走法，**不是 1:1 实测数据**，具体数值因模型 / 数据而异。

- **示例 A — YOLOv8 nv12**：default 跑出 cosine=0.91（未达检测阈值 0.95）。第 1 步校准数据自检 OK。第 2 步切 `calibration_type: mix` 后 cosine=0.96 ✓。**收工**。
- **示例 B — ResNet50 分类**：default cosine=0.94（未达分类阈值 0.99）。第 2 步 `mix` / `kl` / `max` 全试，最高 0.955 仍不够。第 3 步 `accuracy_debug` 显示尾部 `Gemm_99` 敏感度最低（cosine 0.78），yaml `node_info` 给它加 `'ON': 'CPU'` 回退后整体 cosine=0.98 ✓。
- **示例 C — 自定义 Transformer**：default cosine=0.70（远低于阈值）。第 2 步切完所有 `calibration_type` 提升有限（最高 0.83）。第 3 步 `accuracy_debug` 发现 LayerNorm 周边十几个算子都敏感，逐个调成本太高。第 4 步开主导算子批量 int16（`optimization: set_MatMul_input_int16,set_MatMul_output_int16,set_Add_input_int16,set_Add_output_int16,...`），cosine=0.91，仍不够。第 5 步切 featuremap 路径，cosine 跳到 0.97 ✓。**复盘结论**：根因是 nv12→YUV 转换对 Transformer 输入的精度损失（Transformer 对输入扰动远敏感于 CNN），部署侧若不能接受 featuremap 的预处理开销，需要回头跑 QAT。
- **示例 D — 检测模型 cosine 双低（nv12 与 featuremap 都 <0.9）**：两个路径都低，按 §5.4 表，锅不在颜色空间。回到 §1 检查校准数据，发现校准集 50 张全是白天街景，而验证集含 30% 夜景。把校准集扩到包含夜景的 60 张后 cosine=0.97 ✓。

---

## 7. 交叉引用

| 想做 | 看哪里 |
|---|---|
| `calibration_type` / `optimization` / `node_info` / `input_type_rt` 等字段的完整语义和取值 | `yaml-reference.md` |
| 校准数据集如何准备（nv12 / yuv444 / rgb 脚本） | `calibration.md` |
| cosine 阈值定义、`hb_verifier` 用法、板端 / ONNX 精度对比方法 | `accuracy.md` |
| OE 1.2.8 docker 环境、`hb_mapper` 安装 | `setup.md` |
| `hb_mapper makertbin` 编译报错、运行时 hbm 加载失败 | `troubleshooting.md` |
| QAT 量化感知训练（PTQ 全部走完仍不达标的最终兜底） | Horizon Plugin Pytorch 官方文档（OE 范畴外） |
