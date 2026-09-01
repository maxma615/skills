# hb_mapper makertbin yaml 配置完整参考

> **何时读**：
> 1. SKILL.md 中的 4 个 must-change 字段不足以覆盖你的场景（例如多输入模型、非图像输入、需要 int16 精度兜底、需要指定算子在 BPU/CPU 上运行）。
> 2. 出现 yaml 校验报错、`hb_mapper checker` 通过但 `makertbin` 阶段失败，需要逐字段排查。
> 3. 想在 Model Zoo 默认模板基础上做精度/性能调优（如 `optimization`、`calibration_type`、`compile_mode` 切换）。
>
> **来源**：`D:/20_Dev_Projects/29_Skills/YOLO/artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_makertbin.rst.txt`（OpenExplorer v1.2.8，X5 / `march: bayes-e`）。

## 目录

1. [`model_parameters`](#1-model_parameters)
2. [`input_parameters`](#2-input_parameters)
3. [`calibration_parameters`](#3-calibration_parameters)
4. [`compiler_parameters`](#4-compiler_parameters)
5. [输入类型完整矩阵](#5-输入类型完整矩阵)
6. [常用 optimization 选项](#6-常用-optimization-选项)
7. [`custom_op` 自定义算子参数组](#7-custom_op-自定义算子参数组)
8. [多输入与 param_value 写法](#8-多输入与-param_value-写法)

---

## 1. `model_parameters`

| 参数 | 类型 | 默认 | 含义 / 何时改 |
|---|---|---|---|
| `onnx_model` | str | 无 | ONNX 浮点模型路径；`--model-type onnx` 时**必填**。 |
| `prototxt` | str | 无 | Caffe 模型 prototxt 路径；`--model-type caffe` 时**必填**，ONNX 流程忽略。 |
| `caffe_model` | str | 无 | Caffe `.caffemodel` 文件；`--model-type caffe` 时**必填**。 |
| `march` | str | 无 | 目标 BPU 微架构。**X5 固定写 `bayes-e`**；`bayes`=J5，`bernoulli2`=X3/J3。 |
| `output_model_file_prefix` | str | `'model'` | 产出 `.bin` 的文件名前缀。建议带上模型名+分辨率+输入格式，便于区分版本。 |
| `working_dir` | str | `'model_output'` | 编译产物输出目录；不存在会自动创建。 |
| `layer_out_dump` | bool | `False` | 是否保留每层中间结果；**仅 debug 用**，开启后无法配合 `input_source=resizer`。 |
| `output_nodes` | str | 无 | 强制指定模型的输出节点名；多个用 `;` 分隔。用于裁剪模型尾部或调试。 |
| `remove_node_type` | str | 无 | 按算子类型批量删除模型首尾节点；取值范围 `Quantize / Dequantize / Transpose / Cast / Reshape / Softmax`，多类型用 `;` 分隔。**仅作用于输入/输出端的节点**，删除顺序敏感。 |
| `remove_node_name` | str | 无 | 按节点名删除模型首尾节点；多名用 `;` 分隔。约束同 `remove_node_type`。 |
| `set_node_data_type` | str | 无 | 指定算子输出数据类型为 int16（满足约束时）。**已合并到 `node_info`，新项目用 `node_info` 即可**。 |
| `debug_mode` | str | 无 | 取值 `"dump_calibration_data"`：保存 `.npy` 格式的校准数据，供精度 debug 工具消费。 |
| `node_info` | dict/str | 无 | 综合算子级控制：①指定 BPU/CPU；②指定输入/输出 int16；③对单输入用 `InputType0/1/...`。详见官方文档。**取代了 `set_node_data_type` / `run_on_cpu` / `run_on_bpu`**。 |

`node_info` 典型写法：

```yaml
node_info: {
  "node_name": {
    'ON': 'BPU',
    'InputType': 'int16',
    'OutputType': 'int16'
  }
}
# 或简写：
node_info: 'node_name1:int16;node_name2:int16'
```

---

## 2. `input_parameters`

| 参数 | 类型 | 默认 | 含义 / 何时改 |
|---|---|---|---|
| `input_name` | str | 无 | 输入节点名；**单输入可留空 `""`**，多输入用 `"in1;in2;in3"`，顺序决定后续所有 list-like 参数的顺序。 |
| `input_type_train` | str | 无（**必填**） | 原始浮点模型期望的输入格式：`rgb / bgr / yuv444 / gray / featuremap`。 |
| `input_layout_train` | str | 无（**必填**） | 原始浮点模型的数据排布：`NCHW / NHWC`。必须与训练时一致。 |
| `input_type_rt` | str | 无（**必填**） | 板端实际喂入的格式：`rgb / bgr / yuv444 / nv12 / gray / featuremap`。和 `input_type_train` 的合法组合见第 5 节矩阵。 |
| `input_layout_rt` | str | 无 | 板端期望的排布；`input_type_rt=nv12` 时**不需要配置**，由工具确定。 |
| `input_space_and_range` | str | `'regular'` | YUV420 子制式：`regular`（[0,255]）或 `bt601_video`（[16,235]）；**仅 `nv12` + `input_type_train ∈ {rgb,bgr}` 时生效**。 |
| `input_shape` | str | 无 | 输入尺寸，维度以 `x` 连接，如 `'1x3x224x224'`；单输入可省略（自动从模型读）。 |
| `input_batch` | int | `1` | 部署 batch；取值 `1-4096`。**仅 `input_shape` 第一维=1 且原模型支持多 batch 时生效**；多输入模型作用于所有输入。 |
| `norm_type` | str | `'no_preprocess'` | 在模型内部插入的预处理类型：`no_preprocess / data_mean / data_scale / data_mean_and_scale`。详见下表。 |
| `mean_value` | str | 无 | 单值表示所有通道共用；按通道则用空格分隔，如 `'103.94 116.78 123.68'`；某输入不需要时填 `'None'`。`norm_type` 含 `data_mean*` 时必填。 |
| `scale_value` | str | 无 | 与 `mean_value` 同规则；`norm_type` 含 `data_scale*` 时必填。YOLO 常用 `0.003921568627451`（即 `1/255`）。 |

### `norm_type` 的 4 种取值

| 取值 | 行为 | 典型场景 |
|---|---|---|
| `no_preprocess` | 不插入任何预处理；校准 bin 已经是 float32 归一化数据 | **featuremap 输入**（语音、雷达、已归一化的特征图）；`input_type_rt=featuremap` 非四维时**必须**此值 |
| `data_scale` | 仅乘 `scale_value`；常用于把 uint8 [0,255] 缩放到 [0,1] | **YOLO 默认路线**：`scale_value=1/255 ≈ 0.003921568627451` |
| `data_mean` | 仅减 `mean_value` | 少数只做去均值的模型 |
| `data_mean_and_scale` | 先减 `mean_value`、再乘 `scale_value`（标准 ImageNet 归一化） | **ResNet / ViT / ConvNeXt** 等 ImageNet 训练的模型：`mean=103.94 116.78 123.68`，`scale=0.017` |

---

## 3. `calibration_parameters`

| 参数 | 类型 | 默认 | 含义 / 何时改 |
|---|---|---|---|
| `cal_data_dir` | str | 无 | 校准数据目录；`calibration_type` 非 `load/skip` 时**必填**。多输入按 `input_name` 顺序提供多个目录，用 `;` 分隔。文件夹后缀 `_f32` 时自动按 float32 解释。 |
| `cal_data_type` | str | 无（强烈建议显式写） | 校准 bin 的数据存储类型：`float32 / uint8 / int32 / int16 / int8`。**Model Zoo 默认管线必须 `float32`**。未指定时按目录后缀推断。 |
| `preprocess_on` | bool | `False` | `True` 时让工具用 skimage 自动 resize 校准图（仅 4 维图像模型）。**生产环境建议关闭**，自己离线生成 bin 更可控。 |
| `calibration_type` | str | `'default'` | 校准算法；可选 `default / mix / kl / max / load / skip`。详见下表。 |
| `max_percentile` | float | `1.0` | 仅 `calibration_type=max` 时生效，取值 `0.5~1.0`；常用 `0.99999/0.99995/0.99990/0.99950/0.99900` 削顶。 |
| `per_channel` | bool | `False` | 是否对 featuremap 按通道校准；`calibration_type` 非 `default/mix` 时生效。精度不达标时可尝试开启。 |
| `run_on_cpu` | str | 无 | 强制指定算子在 CPU 运行（牺牲性能换 float 精度）。**已合并到 `node_info`**。 |
| `run_on_bpu` | str | 无 | 强制指定算子在 BPU 运行（接受量化损失换性能）。**已合并到 `node_info`**。 |
| `optimization` | str/list | 无 | 调优开关组合；详见第 6 节。 |

### `calibration_type` 选择

| 取值 | 含义 | 何时用 |
|---|---|---|
| `default` | 自动搜索：内部尝试 KL/Max 等组合并挑最优；**首选** | **第一次量化总是先用 `default`**，省心 |
| `mix` | 多方法搜索 + 节点级敏感度分析，从不同方法中按节点挑最佳，组合成融合校准 | `default` 精度不够时的下一步尝试；编译时间显著变长 |
| `kl` | KL 散度算法 | 已知模型对 KL 友好（经典 CNN）或想复现某些社区结果 |
| `max` | Max（可配 `max_percentile` 削顶） | 输出分布有极端长尾时；配合 `max_percentile=0.99995` 等手动调节 |
| `load` | 加载 QAT plugin 导出模型的已有校准数据 | **使用 QAT 量化感知训练流程**时**必须**此值 |
| `skip` | 内部随机数 + max 校准，不需要 `cal_data_dir` | **仅验证模型能否走通编译/跑通性能评测**；得到的 bin 不可用于精度验证 |

---

## 4. `compiler_parameters`

| 参数 | 类型 | 默认 | 含义 / 何时改 |
|---|---|---|---|
| `compile_mode` | str | `'latency'` | 编译策略：`latency`（最低延迟）/ `bandwidth`（最低 DDR 带宽）/ `balance`（需配 `balance_factor`）。**绝大多数模型保持 `latency`**。 |
| `balance_factor` | int | 无 | 取值 `0-100`；`compile_mode=balance` 时**必填**。`0` ≈ bandwidth，`100` ≈ latency。 |
| `debug` | bool | `True` | 把静态分析的 per-layer 性能写进 bin 模型，可在 `hb_perf` 产物的 HTML 中查看每层计算量/搬运耗时。**生产建议保持 True**。 |
| `core_num` | int | `1` | BPU 核心数。**X5 仅支持 `1`**（OE 1.2.8 文档明确限制）；J5 等多核平台才可填 `2`。 |
| `optimize_level` | str | `'O0'` | 编译优化等级 `O0~O3`。**生产/性能评测必须 `O3`**；调试期可用 `O0/O1` 加快编译。 |
| `input_source` | dict | 自动 | bin 模型输入数据来源：`ddr / pyramid / resizer`。`input_type_rt=nv12/gray` 默认 `pyramid`，其余默认 `ddr`；`resizer` 仅支持 `nv12/gray`，写法如 `{"data": "ddr"}`。 |
| `max_time_per_fc` | int | `0` | 单个 function-call 最大执行时间（μs），取值 `0` 或 `1000-4294967295`；**仅板端模型抢占功能需要**，模拟器无效。 |
| `jobs` | int | 无 | 编译并行进程数；填机器核心数以内的值（Model Zoo 用 `2`）。仅影响编译速度，不影响产物。 |
| `advice` | int | 无 / `0` | 当某 op 实际计算耗时与理论值偏差超过该 μs 阈值时打印诊断 log（含 padding 比例）。仅排查性能异常时用。 |

---

## 5. 输入类型完整矩阵

合法的 `input_type_rt` × `input_type_train` 组合（Y=支持，N=不支持）：

| input_type_train \ input_type_rt | nv12 | yuv444 | rgb | bgr | gray | featuremap |
|---|---|---|---|---|---|---|
| yuv444     | Y | Y | N | N | N | N |
| rgb        | Y | Y | Y | Y | N | N |
| bgr        | Y | Y | Y | Y | N | N |
| gray       | N | N | N | N | Y | N |
| featuremap | N | N | N | N | N | Y |

典型组合速查：

| input_type_rt | input_type_train | norm_type | 校准 bin 内容 | 何时用 |
|---|---|---|---|---|
| `nv12` | `rgb` | `data_scale`（1/255） | uint8 → float32 [0,255]，NCHW，RGB 顺序 | **YOLO 默认**；板端摄像头 ISP 直接喂 NV12 |
| `nv12` | `bgr` | `data_scale` | 同上但 BGR 顺序 | OpenCV/Caffe 训练流程（BGR 输入），板端走 ISP |
| `rgb`  | `rgb` | `data_scale` | 同上 | 板端已有解码后的 RGB（注意板端模型输入数据类型会被强制为 int8，需 -128，API 内部已处理） |
| `bgr`  | `bgr` | `data_scale` | 同上 BGR | 同上 |
| `yuv444` | `rgb` | `data_scale` | 同上 | 视频源直接给 YUV444 的特殊场景 |
| `gray` | `gray` | `data_scale` | 单通道 uint8 → float32 | 灰度模型；板端可只取 NV12 的 Y 通道地址作为输入 |
| `featuremap` | `featuremap` | `no_preprocess` | 已归一化的 float32，按训练 layout 摆放 | **精度兜底 / 语音 / 雷达 / 已归一化的特征图输入** |

补充约束：

- `input_type_rt=nv12` 时输入尺寸 **不能有奇数**（H、W 都必须偶数）。
- `input_space_and_range='bt601_video'` 仅在 `input_type_rt=nv12` 且 `input_type_train ∈ {rgb,bgr}` 时支持。
- `input_type_rt ∈ {rgb,bgr}` 的板端模型输入数据类型为 `int8`，常规图像数据需 `-128`（API 已封装，无需手动处理）。
- `input_type_rt=featuremap` 且非四维时，`norm_type` 必须为 `no_preprocess`。
- `input_type_rt` 与 `input_type_train` 配置成相同值即直通处理，不影响性能。

---

## 6. 常用 optimization 选项

`optimization` 取值可单填也可逗号串联，常用项：

| 取值 | 作用 | 典型场景 |
|---|---|---|
| `set_Softmax_input_int8,set_Softmax_output_int8` | 把 Softmax 从 CPU float 量化为 BPU int8 计算（两者等价，写一个即可） | **Model Zoo YOLO 默认管线**：消除尾部 CPU 节点，提升板端帧率 |
| `set_model_output_int8` | 模型输出整体设为 int8 低精度输出 | 极致带宽优化 / 板端只关心 argmax 等结果 |
| `set_model_output_int16` | 模型输出整体设为 int16 低精度输出 | 比 int8 多一点精度的同时仍省带宽 |
| `set_{NodeKind}_input_int16` | 把某类算子（按标准 ONNX 算子名 `Conv/Mul/Sigmoid/...`，区分大小写）输入量化为 int16，不支持时自动回退 int8 并打 log | 局部精度调优；常用于敏感算子 |
| `set_{NodeKind}_output_int16` | 同上，作用于输出 | 同上 |
| `asymmetric` | 启用非对称量化 | 部分模型可提精度。**`calibration_type=default` 时由算法自动选，无法显式配置** |
| `bias_correction` | 启用 BiasCorrection 量化算法 | 部分模型精度可提升 |
| `lstm_batch_last` | 把 LSTM 的 batch 维转到 W 维，更贴合 X5 BPU 硬件 | **仅 X5**，LSTM batch-input size 较大时；不保证一定加速 |

> 精度掉点时的 `calibration_type` / `optimization` / `node_info` 组合调优策略 → 详见 `accuracy-tuning.md`。
>
> 关于 `node_info` 的 int16 配置语义与回退规则、各算子的 int16 支持情况，详见官方文档「工具链算子支持约束列表」和「int16 配置说明」章节。

---

## 7. `custom_op` 自定义算子参数组

| 参数 | 类型 | 默认 | 含义 / 何时改 |
|---|---|---|---|
| `custom_op_method` | str | 无 | 自定义算子策略；当前仅支持 `register`。详见官方文档「自定义算子开发」。 |
| `op_register_files` | str | 无 | 自定义算子的 Python 实现文件名；多个用 `;` 分隔。 |
| `custom_op_dir` | str | 无 | 自定义算子 Python 实现文件所在目录；与工作目录同级可省略。**必须用相对路径**。 |

> 仅当模型中含工具链不支持的算子、且决定自己实现 CPU 兜底时才需要这一组。日常 YOLO / ResNet / ViT 等用不到。

---

## 8. 多输入与 param_value 写法

### 基本规则

- 单值：`param_name: 'value'`
- 多值（多输入或通道维数据）：`param_name: 'v1; v2; v3'`，**用 `;` 分隔，顺序必须与 `input_name` 严格一致**。
- `mean_value` / `scale_value` 内部多通道值用**空格**分隔（与外部 `;` 分隔不同）。例：`mean_value: '103.94 116.78 123.68; 0.0 0.0 0.0'` 表示两个输入，第二个无均值。
- 某输入不需要 mean/scale 时为该位填 `'None'`。

### 多输入完整示例（图像 + featuremap 混合输入）

```yaml
input_parameters:
  input_name: 'image; feat'
  input_type_train: 'rgb; featuremap'
  input_layout_train: 'NCHW; NCHW'
  input_type_rt: 'nv12; featuremap'
  input_shape: '1x3x224x224; 1x256x14x14'
  norm_type: 'data_scale; no_preprocess'
  scale_value: '0.003921568627451; None'
  mean_value: 'None; None'

calibration_parameters:
  cal_data_dir: './cal_image_f32; ./cal_feat_f32'
  cal_data_type: 'float32; float32'
  calibration_type: 'default'
```

> 多输入时**强烈建议显式写出 `input_shape`**，避免依赖自动推断导致参数错位。

### int16 配置补充

- `node_info` 标 op 输入/输出 int16 后，工具会检查上下游算子是否支持以 int16 计算；**不支持的会自动回退 int8 并打 log**，所以可以放心试。
- `OutputType` 作用于该算子的**所有输出**，不支持 `OutputType0/1`；`InputType` 支持 `InputType0/InputType1/...` 指定第几个输入。
- 全模型 int16（在 `optimization` 中开 `set_*_input_int16/set_*_output_int16` 覆盖主要算子类型）会让 bin 体积 ≈2×、推理慢 30-50%，仅做精度兜底用。

### 易踩坑速查

- `input_type_rt: nv12` 时 H/W **不能有奇数**；常见的 `1x3x320x320` 可以，`1x3x319x320` 会编译失败。
- `core_num` 在 X5 上**只能填 1**；从 J5 yaml 迁移过来时记得改回 1。
- `optimize_level` 默认是 `O0`，**不改就拿不到正常性能**；生产/性能评测必须 `O3`。
- `calibration_type: skip` 产出的 bin **不能用于精度验证**，只能做流程验证或性能 demo。
- `cal_data_type` 不写时按目录后缀（`_f32` → float32，否则 uint8）猜测；**Model Zoo 默认管线必须显式写 `float32`**。
- `layer_out_dump: True` 与 `input_source: resizer` **互斥**。
