# 报错与故障排查手册

> **何时读**：`hb_mapper checker` / `hb_mapper makertbin` / `hb_model_modifier` / `hb_verifier` / `hb_onnxruntime` / 板端 libDNN 报错 → 来这里按报错文本搜。先找文本，再读"可能原因 → 解决建议"。如果走完精度调优（`accuracy-tuning.md`）或性能调优（`performance.md`）流程都不奏效，本文末尾"诊断思路"章节给出根因排查路径。
>
> **来源**：
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_faq_troubleshooting/troubleshooting.rst.txt`（常见故障处理全集）
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_faq_troubleshooting/ptq_faq.rst.txt`（PTQ 常见问题）
>
> 本文按工具分组列错误现象 / 可能原因 / 解决建议。yaml 字段语义见 `yaml-reference.md`；环境安装错误见 `setup.md`；精度低问题先看 `accuracy.md` / `accuracy-tuning.md`；性能问题看 `performance.md`。

---

## 0. 三阶段错误定位

按工具链调用顺序，错误分三大类：

```
浮点 ONNX
  │
  ├── ① hb_mapper checker      → §1 检查阶段错误（最早暴露，最易修）
  │       · 算子不支持 / 自定义算子未注册
  │       · 动态 shape 没指定 input-shape
  │       · CPU 算子工具链不支持
  │
  ├── ② hb_mapper makertbin    → §2 编译阶段错误（最复杂）
  │       · 算子参数超约束 → CPU 回退（多数情况可忽略）
  │       · onnxruntime 不支持 / opset 版本不对 / shape inference 失败
  │       · 量化 / 编译 core dump
  │       · BPU 无可量化节点 / 双核编译报错
  │
  ├── ③ hb_model_modifier      → §3 模型修改错误
  ├── ④ hb_verifier            → §4 验证比对失败
  ├── ⑤ hb_onnxruntime         → §5 ONNX 推理类报错
  └── ⑥ libDNN（板端）         → §6 上板运行时报错
```

每段都给出报错文本 + 原因 + 解决方案。文本能复制就直接复制——很多报错日志带 `{op_name}` / `{op_type}` 占位符，搜索时用关键字段就行（如 `"only support 4 dim"`、`"Unsupported op"`）。

---

## 1. `hb_mapper checker` 报错

`hb_mapper checker` 是模型转换之前的检查，会简化跑一遍完整流程，输出算子能否进 BPU。

### 1.1 `ERROR The shape of model input:input is [xxx] which has dimensions of 0`

```
ERROR The shape of model input:input is [xxx] which has dimensions of 0.
Please specify input-shape parameter.
```

**原因**：浮点 ONNX 是动态 shape（某一维写的 `?` 或 `-1`）。

**解决**：`hb_mapper checker` 命令加 `--input-shape "input_name input_shape"`，例如：

```bash
hb_mapper checker --input-shape "images 1x3x640x640" --model yolov8s.onnx --march bayes-e
```

yaml 里也同步配 `input_parameters.input_shape: '1x3x640x640'`。

### 1.2 `ERROR HorizonRT not support these cpu operators: {op_type}`

**原因**：用了工具链不支持的 CPU 算子。

**解决**：查"工具链算子支持约束列表"，把模型里的 `{op_type}` 替换为 BPU/CPU 支持的等效算子。若该算子是模型核心组件，找地平线评估。

**特例 — `GridSample`（`horizon::GridSample`）**：
Deformable Attention 模型（DEIMv2、DAB-DETR 等）导出的 ONNX 含 `horizon::GridSample`（Horizon 自定义算子）。通过 yaml `node_info` 将其或其上游节点设为 `'ON': 'CPU'` 时，HorizonRT v1.2.8 仍会报此错，bin 无法生成。根本原因是 `horizon::GridSample` 无 CPU kernel。
- **不要尝试**用图手术替换成标准 ONNX GridSample：标准 GridSample op 从 opset 16 才引入，OE v1.2.8 最大支持 opset 11，checker 会拒绝（`shape_inference failed`）。
- **实际可行路径**：升级 OE 工具链（官方 v1.2.10+ 若支持）/ QAT 微调 / 换不含 Deformable Attention 的模型。详见 §10。

### 1.3 `Unsupported op {op_type}`（**Warning，可能可忽略**）

**原因**：某 BPU 算子工具链暂不支持（会被回退到 CPU）。

**解决**：
- 若上板整体性能可以接受 → **忽略**该警告。
- 若性能不达标 → 查算子约束列表替换算子（参考 `performance.md` §5.2 删 Quantize/Dequantize 等手段）。

### 1.4 `ERROR nodes:['{op_type}'] are specified as domain:xxx, which are not supported by official onnx`

**原因**：模型包含自定义算子（`domain` 不是官方 ONNX domain）。

**解决**：
- 用官方算子替换。
- 或者按"自定义算子开发"流程注册：https://developer.horizon.cc/forumDetail/71036525692881018

---

## 2. `hb_mapper makertbin` 报错

编译阶段最复杂，按报错关键字定位：

### 2.1 算子约束超限 → CPU 回退

```
Layer {op_name}
  xxx expect data shape range:[[xxx][xxx]], but the data shape is [xxx]
Layer {op_name}
  Tensor xxx expects be n dimensions, but m provided
```

**原因**：`{op_name}` 算子参数超出 BPU 约束，工具链自动回退到 CPU 计算。

**解决**：
- 性能可接受 → **忽略**。
- 性能不达标 → 调整浮点模型 → 把 `{op_name}` 参数压到 BPU 支持范围内 → `hb_mapper checker` 重新验证。

### 2.2 算子优化失败

```
ERROR There is an error in pass: {op_name}. Error message: xxx
```

**原因**：`{op_name}` 算子在 pass 优化阶段失败。

**解决**：收集模型 + `.log` 提交给地平线技术支持。

### 2.3 onnxruntime 不支持

```
Error There is an error in pass: constant_folding.
Error message: Could not find an implementation for the node {op_name}
```

**原因**：onnxruntime 暂不支持 `{op_name}` 算子。

**解决**：查算子支持列表用等效算子替换；核心算子联系地平线评估。

### 2.4 模型解析 core dump

```
Start to parse the onnx model
core dump
```

**原因**：ONNX 模型解析失败，最常见原因是导出时只为单个 output/input 节点指定了 name。

**解决**：重新导出 ONNX。规则二选一：
- 完全**不指定** output/input name，让 PyTorch / TF 自动命名。
- **依次为每个** output/input 节点指定 name（不能只指定部分）。

### 2.5 量化 / 编译 core dump

```
Start to calibrate/quantize the model
core dump

Start to compile the model
core dump
```

**原因**：量化或编译失败。

**解决**：收集模型 + `.log` 文件提交给地平线技术支持。

### 2.6 shape 推断失败

```
ERROR model conversion failed: Inferred shape and existing shape differ in dimension x: (n) vs (m)
```

**原因**：ONNX 模型输入 shape 非法，或工具优化 pass 出错。

**解决**：
1. 先用 `onnxruntime` 在 PC 端跑一遍 ONNX 确认其有效性。
2. ONNX 可正常推理仍报错 → 收集模型 + `.log` 提交地平线。

```
ERROR : There is an ERROR during shape inference, ..., The error model has been saved as shape_inference_fail.onnx
```

**原因**：模型非法或工具解析失败。

**解决**：提交 `.log` + `shape_inference_fail.onnx`（工具自动保存）给地平线。

### 2.7 卷积阈值异常

```
WARNING got unexpected input/output/sumin threshold on conv {op_name}! value: xxx
```

**原因**：数据预处理有误，或该节点 weight 值太小/太大。

**解决**：
- 检查校准数据预处理脚本（`calibration.md` §2 的 `prepare_calibration.py`）与训练预处理是否完全一致（`calibration.md` §1）。
- 在浮点模型该节点前后插 BN 算子优化数据分布。

### 2.8 编译器底层失败

```
ERROR hbdk-cc compile hbir model failed with returncode -n
```

**原因**：编译失败。

**解决**：收集模型 + `.log` 提交地平线。

### 2.9 算子维度限制

```
ERROR {op_type} only support 4 dim input
```

**原因**：工具链该算子只支持 4 维输入。

**解决**：调整模型让该算子的输入维度变为 NCHW 4 维。

### 2.10 算子属性不支持

```
ERROR {op_type} Not support this attribute/mode=xxx
```

**原因**：工具链不支持该算子的某属性 / mode。

**解决**：查算子支持列表替换，或联系地平线评估。

### 2.11 没有可量化节点

```
ERROR There is no node can execute on BPU in this model,
please make sure the model has at least one conv node which is supported by BPU.
```

**原因**：模型中没有 BPU 可量化节点（通常意味着没有 Conv）。

**解决**：
- 确认 ONNX 模型有效。
- 确认模型至少有一个 Conv 算子。
- 仍报错 → 提交模型 + `.log`。

### 2.12 opset 版本不对

```
ERROR The opset version of the onnx model is n, only model with opset_version 10/11 is supported
```

**原因**：ONNX opset 版本不在工具链支持范围。

**解决**：重新导出 ONNX，**指定 `opset_version=10` 或 `11`**：

```python
# PyTorch
torch.onnx.export(model, x, "model.onnx", opset_version=11, ...)
```

### 2.13 `run_on_bpu` 失败

**原因**：算子不在 `run_on_bpu` 支持范围。

**解决**：`run_on_bpu` 目前**仅支持**：
- `Relu` / `Softmax` / `Reshape` / `pooling`（maxpool、avgpool 等）
- `CPU*+Transpose` 组合（声明 Transpose 节点名称，把 CPU* + Transpose 一起跑在 BPU 上，`CPU*` 特指 BPU 支持的 op）

若属于上述但仍失败 → 联系地平线分析；若不属于 → 联系地平线评估。

### 2.14 X5 双核编译

```
ERROR unsupported model: BAYES-E not support execute one model on 2core simultaneously now
```

**原因**：X5 不支持单模型双核同时编译。

**解决**：yaml `compiler_parameters.core_num` 设为 `1`：

```yaml
compiler_parameters:
  core_num: 1
```

---

## 3. `hb_model_modifier` 报错

### 3.1 `ERROR Can not find value info {op_name}`

**原因**：OE 1.1.13 及以下版本已知 bug。

**解决**：升级 OE 包到 1.1.14+，或单独升级 `horizon-tc-ui` 到 1.7.8+（本 Skill 默认 OE 1.2.8，已修复）。

---

## 4. `hb_verifier` 报错

### 4.1 `ERROR Quanti onnx and Arm result Strict check FAILED`

**原因**：量化 ONNX 和板端 ARM runtime 推理结果一致性比对失败。

**解决**：收集模型提交地平线。先自查：
- 校准数据预处理是否正确（`calibration.md`）
- 量化模型本身 cosine 是否正常（`accuracy.md`）

---

## 5. `hb_onnxruntime` 报错

### 5.1 输入数据类型不匹配

```
ERROR [ONNXRuntimeError] : 2: INVALID_ARGUMENT : Unexpected input data type.
Actual: (N11onnxruntime17PrimitiveDataTypexxx), expected: (N11onnxruntime17PrimitiveDataTypexxx)
```

**原因**：喂入 ONNX 的数据 dtype 与模型期待不一致。

**解决**：
- **浮点 ONNX** 期待 `float32`。
- **量化后 ONNX**（`*_quantized_model.onnx`）期待 `int8`。

用 [Netron](https://netron.app/) 或 `onnx.load()` 查模型 input 节点的 `tensor_type.elem_type` 确认。

### 5.2 protobuf 版本冲突

```
[libprotobuf FATAL google/protobuf/stubs/common.cc:83] This program was compiled against version 3.6.1 of the Protocol Buffer runtime library,
which is not compatible with the installed version on (3.19.4).
```

**原因**：torch 用的 protobuf 与 horizon 用的 protobuf 版本冲突。

**解决**：把 `from horizon_tc_ui import HB_ONNXRuntime` **放第一行 import**，**在 import torch 之前**：

```python
from horizon_tc_ui import HB_ONNXRuntime   # 必须最先 import
import torch
# ...
```

其他 horizon API 出现相同报错时同等适用。

---

## 6. libDNN（板端）报错

### 6.1 算子属性不支持

```
(common.h:79): HR:ERROR: op_name:xxx invalid attr key xxx
```

**原因**：libDNN 暂不支持该 op 的某个属性（地平线会逐步把此类约束前移到模型转换阶段提醒）。

**解决**：查算子支持列表替换，或联系地平线评估。

### 6.2 数据类型不匹配

```
(hb_dnn_ndarray.cpp:xxx): data type of ndarray do not match specified type. NDArray dtype_: n, given: m
```

**原因**：libDNN 暂不支持该输入类型。

**解决**：查算子支持列表替换，或联系地平线评估。

### 6.3 内存不足

```
(validate_util.cpp:xxx): tensor aligned shape size is xxx, but tensor hbSysMem memSize is xxx,
tensor hbSysMem memSize should >= tensor aligned shape size!
```

**原因**：申请的输入内存不足。

**解决**：
- libDNN ≥ **1.5.4b**：用 `hbDNNTensorProperties.alignedByteSize` 申请内存。
- libDNN < 1.5.4b：用 `aligned shape × sizeof(tensor_type)` 申请。

`hrt_model_exec model_info` 看 model 的 aligned shape。

### 6.4 hbm input names 不匹配

```
(bpu_model_info.cpp:xxx): HR:ERROR: hbm model input feature names must be equal to graph node input names
```

**原因**：`hb_model_modifier` 工具的已知 bug。

**解决**：升级 OE 到 1.1.14+ 或 horizon-tc-ui 到 1.7.8+（OE 1.2.8 已修复）。

---

## 7. PTQ 转换流程的常见疑问

来自官方 FAQ 的高频问题，与"报错"不同——这些是**行为不符合预期**而非"明确报错"。

### 7.1 nv12 模型 `hb_perf` 和 `hrt_model_exec model_info` 显示的输入大小不一致

**现象**：`hb_perf` 显示 NxHxWx3/2，`hrt_model_exec model_info` 显示 NxHxWx3。

**原因**：NV12 是 YUV420SP 格式（摄像头原始输出）。底层硬件拿到 nv12 后**自动转 yuv444** 才进入模型。
- `hb_perf` 显示的是 **nv12 数据大小**（NxHxWx3/2）。
- `hrt_model_exec` 显示的是**模型实际输入大小**（NxHxWx3）。
- 两者描述的是同一物理过程的不同阶段。

**怎么办**：板端按 nv12 H×W×3/2 准备数据即可，**不需要自己转 yuv444**（硬件会做）。

### 7.2 ONNX 与 bin 输入数据排布不一致

**现象**：同一张图喂给 `quanti.onnx` 和 `bin`，结果差异巨大。

**原因**：
- 当 `input_type_rt = nv12`（`input_source = pyramid`）：`quanti.onnx` 输入是 **NHWC**。
- 当 `input_type_rt = yuv444/rgb/bgr`（`input_source = ddr`）：`quanti.onnx` 输入与原浮点模型一致（通常 NCHW）。
- `bin` 的输入排布永远跟 yaml `input_layout_rt` 走。

**怎么办**：
- PC 推 `quanti.onnx` → 用 Netron 看 ONNX 输入 shape 准备数据。
- 板端推 `bin` → 看 yaml `input_layout_rt`，或 `hrt_model_exec model_info` / `hbDNNGetInputTensorProperties()`。
- 对齐两者再做精度比对。

### 7.3 多输入模型转换后输入顺序变化

**现象**：原浮点 ONNX 输入顺序 `input1, input2, input3`，转 bin 后变成 `input3, input2, input1`。

**原因**：多输入模型在 original.onnx → quanti.onnx → bin 各阶段顺序**可能被工具链调整**，属正常现象。

**怎么办**：
- 做精度一致性对齐时，**按节点名匹配**输入数据，而不是按位置。
- 板端查 bin 真实顺序：`hb_model_info <model>.bin` → `input_parameters info` 分组列出的顺序就是 bin 输入顺序。

### 7.4 多 batch 模型怎么编译

**条件**：`input_batch` 参数**仅当 `input_shape` 第一维为 1** 时生效，且原 ONNX 必须支持多 batch 推理。每份校准数据 shape 必须与 `input_shape` 一致。

**动态输入 ONNX**（`? x3x224x224`）：
- 配 `input_shape: '1x3x224x224'` + `input_batch: 4` → 多 batch 模型，校准数据 shape `1x3x224x224`。
- 配 `input_shape: '4x3x224x224'`（直接多 batch）→ **不能用 `input_batch`**，校准数据 shape `4x3x224x224`。

**非动态输入 ONNX**：
- `input_shape[0] = 1` → 可用 `input_batch`，校准数据 shape 与原 ONNX 一致。
- `input_shape[0] > 1` → **不能用 `input_batch`**。

### 7.5 default 校准方式的内部逻辑

`default` 内部三步搜索（**首次跑不达标时，知道这个能帮你判断要切哪种 calibration_type**）：

- **Step 1**：尝试 Max / Max-Percentile 0.99995 / KL 三种，取最高 cosine。若 ≥ 0.995 → 收工；否则进 Step 2。
- **Step 2**：尝试 Max-Percentile 0.99995 + per_channel 组合，若 ≥ 0.995 → 收工；否则进 Step 3。
- **Step 3**：取 Step 2 最优方案，再叠加非对称量化（第 5 种方法），从 5 种方案中选 cosine 最高的。

**含义**：如果 `default` 跑出 cosine 还是低，意味着上述 5 种方案都不够好，需要手动切 `mix` 或 `kl`（见 `accuracy-tuning.md` §2）。

### 7.6 mix 校准方式的内部逻辑

- **Step 1**：用 KL 跑一遍，按节点 cosine 找出"量化敏感节点"。
- **Step 2**：对每个敏感节点，单独尝试 Max / Max-Percentile 0.99995 / KL 三种，选每节点最佳。
- **Step 3**：评估 Mix vs Max vs Max-Percentile 0.99995 vs KL 的累积误差，输出最优。

**含义**：mix 比 default 更彻底，但编译耗时更长；敏感算子聚集时收益最大。

### 7.7 为什么尾部可加速算子也跑在 CPU 上

**现象**：模型尾部明明是 Conv+ReLU，转完发现 ReLU 跑在 CPU 上。

**原因**：
- X5 工具链只允许**模型尾部的 Conv 以 int32 高精度输出**，其他算子只能 int8 输出。
- 通常 Conv+BN+ReLU 会融合，但**尾部 int32 输出的 Conv 不参与融合**。
- 所以尾部 Conv 保留 int32 高精度，ReLU/ReLU6 必须独立跑（int8 输出），但 int8 ReLU 在 BPU 实现成本高 → 默认放 CPU。

**怎么办**：
- 精度优先 → 默认即可（精度更好）。
- 性能优先 → yaml 给该 ReLU 加 `run_on_bpu`，但有精度损失（见 §2.13 支持范围）。

### 7.8 主动量化 vs 被动量化

**现象**：明明算子符合 BPU 约束，转完仍在 CPU 上。

**原因**：算子分**主动量化**（如 Conv 直接硬件支持）和**被动量化**（如 Reshape/Transpose 必须前后都是 BPU 算子才能进 BPU）。如果某 Reshape 上下游不全是 BPU 算子，它就会留在 CPU。

详细原理与排查方法：
https://developer.horizon.cc/forumDetail/118364000835765793

---

## 8. 走完精度 / 性能调优仍解决不了：根因排查思路

如果 `accuracy-tuning.md` 5 步走完精度不达标，或 `performance.md` 决策树走完性能不达标，按以下思路找根因：

### 8.1 先做隔离实验

```
       浮点 ONNX
       │ (用 onnxruntime 验证)
       │
       ▼
   ① 浮点 ONNX 推理是否正确？
       ├── No  → 训练 / 导出 ONNX 阶段有问题（与工具链无关）
       └── Yes
             │
             ▼
   ② *_original_float_model.onnx 与浮点 ONNX 是否一致？
       ├── No  → 工具链 ONNX 预处理 / 数据 pipeline 问题（calibration.md §1）
       └── Yes
             │
             ▼
   ③ quanti.onnx 与浮点 ONNX 输出 cosine 是否达标？
       ├── No  → 量化策略问题（accuracy-tuning.md §2 切 calibration_type）
       └── Yes
             │
             ▼
   ④ bin 与 quanti.onnx 是否一致（hb_verifier）？
       ├── No  → 编译器 bug，提交地平线
       └── Yes
             │
             ▼
   ⑤ 板端 bin 与 PC 端 bin 仿真是否一致？
       ├── No  → 板端环境 / libDNN 版本 / 内存对齐问题（§6）
       └── Yes  → 应用层后处理问题，与工具链无关
```

每一步只用**当前阶段的产物**和**前一阶段的产物**比较，把误差源精确定位到一段流水线内。

### 8.2 提交地平线时需要的资料清单

如果排查后判断是工具链 bug，提交时一并附上：

1. 浮点 ONNX 文件
2. 完整的 yaml 配置文件
3. 重现报错的命令行
4. 完整 `.log` 文件
5. （如有）`shape_inference_fail.onnx` 或 `calibration_data/`
6. OE 版本、Docker 镜像版本、horizon-tc-ui 版本
7. （如能脱敏）少量校准数据样本

### 8.3 升级 OE 通常能解决的问题

部分错误在 OE 老版本里已知，新版本已修：

| 报错 | 修复版本 |
|---|---|
| `hb_model_modifier`: `Can not find value info` | OE 1.1.14 / horizon-tc-ui 1.7.8 |
| libDNN: `hbm model input feature names must be equal to graph node input names` | OE 1.1.14 / horizon-tc-ui 1.7.8 |

本 Skill 默认 OE 1.2.8，以上问题不应再出现。如果遇到 → 检查 docker 镜像是否真是 1.2.8：

```bash
docker images | grep openexplorer
# 期待：openexplorer/ai_toolchain_ubuntu_20_x5_gpu  v1.2.8
```

---

## 9. 交叉引用

| 想做 | 看哪里 |
|---|---|
| 浮点模型预处理是否对齐训练 | `calibration.md` §1 |
| yaml 字段语义全集 | `yaml-reference.md` |
| OE 1.2.8 安装 / Docker 登录 | `setup.md` |
| cosine 度量阈值 / `hb_verifier` 用法 | `accuracy.md` |
| 精度调优决策树（`calibration_type` / `node_info` / featuremap）| `accuracy-tuning.md` |
| 性能评测 / `hb_perf` / `hrt_model_exec perf` / yaml 性能字段 | `performance.md` |
| 算子支持约束列表（什么算子能进 BPU）| 官方 RST `appendix/supported_op_list` |
| 自定义算子开发 | https://developer.horizon.cc/forumDetail/71036525692881018 |
| 主动量化 / 被动量化原理 | https://developer.horizon.cc/forumDetail/118364000835765793 |
| Deformable Attention / Transformer decoder PTQ 已知限制 | §10（本文） |

---

## 10. Deformable Attention / Transformer Decoder PTQ 已知限制（OE v1.2.8）

> **背景**：2026-06 对 DEIMv2-N（HGNetv2-B0 + 3 层 Deformable Cross-Attention decoder）完成完整 PTQ 实验，最终结论：**OE v1.2.8 无法对此类模型做有效 PTQ**。以下适用于所有含 Deformable Cross-Attention decoder 的模型（DEIMv2、DAB-DETR、DINO-DETR 等）。

### 10.1 根本原因

Deformable Cross-Attention 的采样偏移计算链：
```
sampling_offsets/MatMul → Add → Mul → Sub（坐标中心化）
```
`Sub` 节点输出值域为**负值**（偏移量中心化后在 `[-0.5, 0.5]`，减去中心点后出现负值集中区间）。PTQ 校准时 INT8 scale 估算仅覆盖正值域，导致整个采样偏移**符号翻转**（cosine ≈ -0.19），下游所有 GridSample 采样位置全错，模型输出退化为 0 检测。

**这不是校准参数可以修复的问题。** 换 `calibration_type: mix/kl` 均无效。

### 10.2 尝试方案及结论（已全部验证失败）

| 版本 | 方案 | 结果 |
|---|---|---|
| V3 | decoder cross_attn Sub 节点 `ON: CPU` | 编译通过，但 `ON: CPU` 不恢复 float32（见 §10.3），板端 0 检测 |
| V4 | `horizon::GridSample` `ON: CPU` | **编译失败**：`HorizonRT not support these cpu operators: GridSample` |
| V5 | decoder 入口 Reshape `ON: CPU` | 编译通过，板端仍 0 检测（原因同 V3） |
| 图手术 opset 16 | 替换 `horizon::GridSample` → 标准 ONNX GridSample（opset 16） | checker 拒绝：`max supported opset version is 11` |
| 图手术 opset 11 | 保持 opset 11，domain 改空字符串 | checker 拒绝：`shape_inference failed`（opset 11 无 GridSample schema） |

### 10.3 `node_info ON: CPU` 语义澄清

**常见误解**：把节点设为 `ON: CPU` 就是让它以 float32 运行，从而绕过量化精度问题。

**实际语义**：`ON: CPU` 只改变**运行时执行硬件**，不改变量化精度。节点的权重和激活在 `hb_mapper makertbin` 编译阶段已经固化为 INT8；CPU 执行仍使用这些 INT8 值，不会回到 float32。

因此：
- 对 decoder sampling offset Sub 节点设 `ON: CPU` → 该节点在 CPU 上以 INT8 精度执行，符号翻转依然存在
- 对 decoder 入口 Reshape 设 `ON: CPU`（试图把整个 decoder 路由到 CPU）→ 同理，decoder 所有节点仍是 INT8

### 10.4 OE v1.2.8 硬性约束

| 约束 | 说明 |
|---|---|
| `horizon::GridSample` 不能 `ON: CPU` | HorizonRT 无 CPU kernel，报错 `HorizonRT not support these cpu operators: GridSample` |
| ONNX opset 上限 = 11 | 标准 ONNX GridSample 从 opset 16 引入，图手术替换在 opset 11 下不可行 |
| `ON: CPU` 不恢复 float32 | 见 §10.3 |

### 10.5 实际可行路径

| 路径 | 说明 |
|---|---|
| **升级 OE 工具链** | 官方 v1.2.10+ 若支持更高 opset 或新版 GridSample CPU kernel |
| **QAT 微调** | 量化感知训练，避免 PTQ scale 估算错误；需修改训练代码 |
| **换模型架构** | 用不含 Deformable Attention 的检测模型（YOLO 系列、RT-DETR non-deformable 变体）**强烈推荐** |

### 10.6 模型选型建议（OE v1.2.8）

**PTQ 高成功率**：
- YOLO 系列（v5u/v8/v9/v11/v13/YOLO26）— 实测 cosine ≥ 0.99
- RT-DETR（不含 Deformable Attention 的变体）

**PTQ 高风险（含 Deformable Cross-Attention decoder）**：
- DEIMv2 全系列（N/S/M/L/X）
- DAB-DETR、DINO-DETR、Deformable DETR

**快速风险检查**：`hb_mapper makertbin` 产出的 `quant_info.json` 中，若 decoder 中任何 `Sub/Transpose/Split` 节点的 `cosine_similarity` < 0（负值），该模型在 OE v1.2.8 PTQ 下不可用，不要再调 calibration 参数。
