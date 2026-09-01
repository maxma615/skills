---
name: rdk-x5-toolchain-quantization
description: 地瓜 RDK X5 OpenExplorer 工具链（OE v1.2.8）PTQ 量化的**工具链层 Skill**（不含 YOLO 训练 / ROS2 部署，端到端用 RDK YOLO Toolkit）。当需要把任意 ONNX 转成 RDK X5 的 .bin / .hbm 时调用，覆盖：环境（Docker 镜像 / OE SDK / 离线包）、`hb_mapper checker` 算子预检、校准数据（nv12 / featuremap / .rgbchw / .yuv）、yaml 配置（`calibration_type` / `node_info` / `optimization`）、`hb_mapper makertbin` 编译、精度（cosine / `hb_verifier` / `hb_mapper infer`）与性能（`hb_perf` / `hrt_model_exec`）评估、精度调优（敏感算子 / int16 / featuremap 兜底）。模型无关，适用于 YOLO/ResNet/ViT/Transformer 等任意 ONNX。当用户提到 hb_mapper、hb_perf、hrt_model_exec、PTQ、量化 ONNX、转 .bin、转 .hbm、校准数据、calibration_type、featuremap、RDK X5 工具链、OE 1.2.8、精度掉点、cosine 不达标、BPU 利用率 等关键词，或在 RDK X5 部署场景下处理 ONNX → 板端可执行产物时使用。
---

# RDK X5 OpenExplorer 工具链 PTQ 量化

模型无关的 PTQ 量化工作流，把任意 ONNX 转为 RDK X5 可部署的 `.bin` 产物，
基于 D-Robotics OpenExplorer **v1.2.8 (py310)** 工具链。

> **首次使用先装环境**：按 `references/setup.md` 拉好 OE Docker 镜像（CPU 版即够）。所有 `hb_mapper*` / `hb_perf` 命令都必须在 OE Docker 容器内执行；`hrt_model_exec` 是板端工具，需把 `.bin` 拷到板上跑。

## When to use

1. 拿到 ONNX 想转 RDK X5 的 `.bin` / `.hbm`
2. 编写或修改 `hb_mapper makertbin` 的 yaml 配置
3. 量化后 cosine similarity 低 / 板端结果与浮点不一致（精度掉点诊断）
4. `hb_mapper checker` 报算子不支持，需要规避策略
5. 已编译模型性能不达预期，要看 BPU 利用率 / 优化编译策略
6. 准备校准集时不确定格式、数量、归一化对齐
7. OE 工具链环境装不上（Docker / SDK / 依赖冲突）

## When NOT to use

- 端到端 YOLO 训练 → 量化 → 板端 → ROS2 部署：用 `RDK YOLO Toolkit`
- RDK X3 / Ultra / S100 等其它芯片：本 Skill 只针对 X5 OE v1.2.8
- QAT（量化感知训练）：本 Skill 只覆盖 PTQ
- 仅需要 ONNX 导出（不量化）：用 PyTorch / TF 自身工具

## 主流程（5 步）

### Step 1 — `hb_mapper checker` 算子预检 [Docker 内]

```bash
hb_mapper checker --model-type onnx --march bayes-e --model ./your_model.onnx
```

读 `hb_mapper_checker.log` 看 BPU / CPU 算子分布。若出现 "unsupported op"，
查 `references/troubleshooting.md` §1（hb_mapper checker 报错）找规避策略
（替换为等效算子 / 用 yaml `custom_op_method: register` 注册自定义算子）。

### Step 2 — 校准数据准备（默认 nv12 路径，归一化交给 yaml） [开发机，宿主机或容器内均可]

```python
# prepare_calibration.py —— 与 Model Zoo ultralytics_yolo/conversion/mapper.py 一致
import cv2, numpy as np
from pathlib import Path

SRC, OUT = Path('./cal_src'), Path('./calibration_data')
OUT.mkdir(exist_ok=True)
W, H, NUM = 640, 640, 20      # 20 起步；>50 校准会很慢

jpgs = [p for p in SRC.iterdir() if p.suffix.lower() in ('.jpg', '.png', '.jpeg')]
if len(jpgs) > NUM:
    idx = np.random.choice(len(jpgs), NUM, replace=False)
    jpgs = [jpgs[i] for i in idx]

for p in jpgs:
    img = cv2.imread(str(p))                       # BGR uint8 HWC
    x = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)       # → RGB（对齐 input_type_train）
    x = cv2.resize(x, (W, H))                      # 直接 resize（YOLO 训练即如此）
    x = np.transpose(x, (2, 0, 1))                 # HWC → CHW
    x = np.expand_dims(x, 0).astype(np.float32)    # NCHW float32，[0, 255] 原始像素
    x.tofile(OUT / (p.stem + '.rgbchw'))           # raw bytes，不做归一化
```

**关键约束**：

1. **数量**：20 张起步。Model Zoo 警告阈值 `< 20`（校准可能失败）/ `> 50`（耗时长）。
2. **代表性**：从训练/验证集随机采样，覆盖典型场景。不要全简单也不要全 hard case。
3. **预处理对齐**：脚本里的 resize 方式、通道顺序必须与训练时一致。nv12 路径下**归一化不在脚本里做**，由 yaml 的 `norm_type` + `scale_value` 完成。
4. **落盘格式**：每张图一个 raw bytes 文件，`tensor.tofile(path)` 直接写。**不能用 `.npy`**：`.npy` 头部 128 字节会被 `hb_mapper` 当成数据塞进 tensor，校准统计错位。
5. **形状校验**：每个文件大小必须等于 `N×C×H×W×4` bytes。文件后缀仅是惯例（Model Zoo 用 `.rgbchw` 表语义）。

更详细的格式/路径选择 → `references/calibration.md`。

### Step 3 — yaml 配置（4 处必改） [开发机]

```yaml
# RDK X5 OE v1.2.8 — PTQ 默认模板（nv12 部署路径，归一化由 hb_mapper 完成）
# 必改：onnx_model / output_model_file_prefix / cal_data_dir / scale_value（如非 1/255）

model_parameters:
  onnx_model: './your_model.onnx'                            # 必改
  march: 'bayes-e'                                            # X5 固定
  layer_out_dump: False
  working_dir: 'bpu_model_output'
  output_model_file_prefix: 'your_model_bayese_640x640_nv12'  # 必改

input_parameters:
  input_name: ''                                              # 留空 = 自动取 ONNX input
  input_type_rt: 'nv12'                                       # 板端运行时输入类型
  input_type_train: 'rgb'                                     # 训练时输入类型
  input_layout_train: 'NCHW'
  norm_type: 'data_scale'                                     # 归一化交给 hb_mapper
  scale_value: 0.003921568627451                              # 1/255；按训练 std 改

calibration_parameters:
  cal_data_dir: './calibration_data'                          # 必改
  cal_data_type: 'float32'
  calibration_type: 'default'                                 # 掉点严重时换 mix/kl/max/load
  optimization: set_Softmax_input_int8,set_Softmax_output_int8

compiler_parameters:
  jobs: 16                                                    # 编译并行进程数，按机器核心数；Model Zoo 默认用 2
  compile_mode: 'latency'                                     # 推理优先；面积优先用 bandwidth
  debug: true
  optimize_level: 'O3'                                        # O0~O3，O3 最优
```

全字段（70+）/ 输入类型矩阵（nv12 / rgb / bgr / yuv444 / featuremap）→ `references/yaml-reference.md`。

### Step 4 — `hb_mapper makertbin` 编译 [Docker 内]

```bash
hb_mapper makertbin --config config.yaml --model-type onnx
```

产物：

- `<prefix>.bin` — 部署产物
- `<prefix>_quantized_model.onnx` — 定点 ONNX（精度比对用）
- `<prefix>_original_float_model.onnx`、`<prefix>_optimized_float_model.onnx`
- `hb_mapper_makertbin.log` + 编译报告 html

日志阅读 / 编译报错 → `references/troubleshooting.md`。

### Step 5 — 精度 & 性能验证

**精度**（开发机 Docker 内）：

```bash
# 量化 ONNX 推理（注意：必须用 horizon 提供的 hb_mapper infer，不能用裸 onnxruntime
# 因为量化模型含 HzQuantize/HzDequantize 自定义算子）
hb_mapper infer --config config.yaml \
                --model-file <prefix>_quantized_model.onnx \
                --model-type onnx \
                --image-file <input_node_name> sample.rgbchw \
                --input-layout NCHW \
                --output-dir infer_out/

# hb_verifier 端到端校验（quanti.onnx + bin 二选一组合，逗号分隔；-s 用模拟器，-b 板端）
hb_verifier -m <prefix>_quantized_model.onnx,<prefix>.bin -s True -i sample.rgbchw
```

阈值：**分类 cosine ≥ 0.99 / 检测·分割 ≥ 0.95**。不达标 → `references/accuracy-tuning.md`（含 featuremap 兜底路径）。完整精度评估方法（自写 cosine 脚本、`*_original_float_model.onnx` 对比、CI gate）见 `references/accuracy.md`。

**性能（编译期，开发机）**：

```bash
hb_perf <prefix>.bin
# 输出 hb_perf_result/<model_name>/<model_name>.html，含 BPU 利用率 / latency 估算 / 算子耗时分布
```

**性能（板端，可选）**：

```bash
# 注意：所有 hrt_model_exec 参数都是下划线分隔（不是连字符）
hrt_model_exec perf --model_file=<prefix>.bin --core_id=0 --thread_num=1 --profile_path="."
```

详细优化技巧 → `references/performance.md`。

## 何时读 references

| 场景 | 文件 |
|---|---|
| 装 OE / Docker / 文档 | `references/setup.md` |
| 改 yaml 高级字段、切输入类型 | `references/yaml-reference.md` |
| 校准数据格式 / 数量 / featuremap 路径 | `references/calibration.md` |
| 精度评估方法、cosine 阈值（含 Transformer ≥0.95 / Pose ≥0.97） | `references/accuracy.md` |
| **精度掉点调优（核心）** | `references/accuracy-tuning.md` |
| BPU 利用率 / 板端 latency 优化 | `references/performance.md` |
| 编译/校准/部署阶段报错 | `references/troubleshooting.md` |
