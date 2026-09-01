# 性能评测与调优手册

> **何时读**：拿到 `.bin` / `.hbm` 想测真实性能 / 开发机静态分析（`hb_perf`）/ 板端实测（`hrt_model_exec perf`）/ 解读 `profiler.log` / 选 yaml 性能参数 / 定位 BPU vs CPU 瓶颈 / 决定精度与速度的取舍。
>
> **来源**：
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_tool/hb_perf.rst.txt`（hb_perf 工具）
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/runtime/source/tool_introduction/hrt_model_exec.rst.txt`（板端 hrt_model_exec）
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_usage/performance_evaluation.rst.txt`（性能评测流程）
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/tune_content/performance_tune.rst.txt`（PTQ 性能调优总章）
>
> 本文只覆盖**性能视角**——测量方法、yaml 性能旋钮、调优决策。`compiler_parameters` 字段全集语义见 `yaml-reference.md`；CPU 算子能否进 BPU 的判定见官方"工具链算子支持约束列表"；精度调优看 `accuracy-tuning.md`；编译 / 运行报错看 `troubleshooting.md`。

---

## 1. `hb_perf` 开发机侧静态分析

不上板就能拿到 BPU 部分的预期性能（**不含 CPU 计算评估**）。适合编译后第一步快速看模型结构是否合理、BPU 子图切分是否符合预期。

### 1.1 用法

```bash
hb_perf <model>.bin
# pack 后的模型要加 -p
hb_perf -p <pack_model>.bin
```

产物：当前目录 `hb_perf_result/<model_name>/`

```
hb_perf_result/
└── mobilenetv1_224x224_nv12/
    ├── mobilenetv1_224x224_nv12.html   ← 主页面
    ├── mobilenetv1_224x224_nv12.png
    ├── MOBILENET_subgraph_0.html        ← 子图明细
    ├── MOBILENET_subgraph_0.json
    └── temp.hbm
```

### 1.2 主页面三部分

**Model Performance Summary**（整体）：

| 指标 | 说明 |
|---|---|
| Model Name | 模型名 |
| BPU Model Latency(ms) | BPU 单帧计算耗时（**不含 CPU**） |
| Total DDR (loaded+stored) bytes per frame (MB per frame) | 单帧 BPU 部分总 DDR 带宽 |
| Loaded Bytes per Frame | 单帧读取数据量 |
| Stored Bytes per Frame | 单帧存储数据量 |

**Details**（每个 BPU 子图）：

| 指标 | 说明 |
|---|---|
| Model Subgraph Name | 子图名 |
| Model Subgraph Calculation Load (OPpf) | 子图单帧计算量 |
| Model Subgraph DDR Occupation (Mbpf) | 子图单帧读写量（MB） |
| Model Subgraph Latency(ms) | 子图单帧耗时 |

**BIN Model Structure**：bin 模型可视化，**深色节点 = BPU，灰色节点 = CPU**。一眼看出哪些层留在 CPU、子图怎么被打断——CPU 节点出现在中间意味着 BPU 子图被切碎，是性能问题的早期信号。

### 1.3 Layer Details（必须开 `debug: True`）

子图明细页 (`*_subgraph_*.html`) 的 Layer Details 表只在 yaml `compiler_parameters.debug: True` 时才有数据：

| 列 | 说明 |
|---|---|
| layer | 算子名 |
| ops | 计算量 |
| original output shape | 原始输出 shape |
| aligned output shape | 对齐后 shape（量化加 padding 用） |
| computing cost (no DDR) | 纯计算耗时 |
| load/store cost | 数据搬运耗时 |
| active period of time | 编译后活跃时间段（不等于执行时间，多个 layer 经常交替/并行）|

> `debug: True` 是 Model Zoo 模板默认值——除非确定生产中体积敏感，**保留即可**。打开它对性能无影响，只增加 bin 元数据。

### 1.4 局限

- 只覆盖 BPU；CPU 算子的耗时根本不进结果——**模型里有任何非首尾的 CPU 节点都必须上板实测**。
- 静态分析是 BPU 理论上限，板端实际会受调度 / 排队 / 内存压力影响略低。

---

## 2. `hrt_model_exec` 板端实测

工具在板端，三个子命令：

| 子命令 | 用途 | 是否需要输入数据 |
|---|---|---|
| `model_info` | 看模型输入输出 `hbDNNTensorProperties` | 否 |
| `infer` | 单帧推理验证 | **需要** `--input_file` |
| `perf` | 多帧性能评测 | 否（工具自动构造随机 tensor）|

### 2.1 `model_info` — 看 shape / layout / dtype

```bash
hrt_model_exec model_info --model_file=mobilenetv1.bin
# pack 模型 / 多模型
hrt_model_exec model_info --model_file=a.bin,b.bin --model_name=a
```

部署前先跑这条确认模型期待的输入格式（NCHW / NHWC、nv12 / featuremap、对齐要求）——很多板端 hang/crash 是输入 layout 不对引起的。

### 2.2 `infer` — 单帧验证

```bash
hrt_model_exec infer --model_file=mobilenetv1.bin --input_file=test.jpg
```

工具会按模型期待 resize 图片，单线程推一帧，输出 latency。用于"我提供的预处理对不对"。

输入文件后缀必须是 `bin/jpg/jpeg/png/JPG/JPEG/PNG`（图片）或 `bin/txt`（feature）。多输入用英文逗号隔开：`--input_file=xxx.jpg,input.txt`。

### 2.3 `perf` — 性能评测（最常用）

**测真实 Latency**（无资源抢占）：

```bash
./hrt_model_exec perf --model_file=mobilenetv1.bin \
    --core_id=0 \
    --frame_count=200 \
    --thread_num=1 \
    --profile_path="."
```

**测极限 FPS**（线程数调大，充分占满 BPU 核心）：

```bash
./hrt_model_exec perf --model_file=mobilenetv1.bin \
    --core_id=0 \
    --frame_count=1000 \
    --thread_num=4 \
    --profile_path="."
```

关键参数：

| 参数 | 默认 | 备注 |
|---|---|---|
| `model_file` | 必填 | .bin 路径 |
| `model_name` | — | 单模型可省 |
| `core_id` | `0` | `0` 任意核 / `1` core0 / `2` core1；X5 仅 `0`/`1` |
| `frame_count` | `200` | 推理帧数（`perf_time` 为 `0` 时生效）|
| `perf_time` | `0` | 分钟；>0 时按时间跑，`frame_count` 失效 |
| `thread_num` | `1` | `[1,8]`。**测 latency 用 1**（无抢占）；**测 FPS 用 >2**（吃满 BPU）|
| `profile_path` | 关 | 设 `"."` 在当前目录产 `profiler.log` + `profiler.csv` |

实时观察 BPU 利用率（另起 shell）：

```bash
hrut_somstatus -n 10000 -d 1
```

### 2.4 控制台输出

```
Running condition:
  Thread number is: 4
  Frame count   is: 1000
  Program run time: 279.004000 ms
Perf result:
  Frame totally latency is: 1084.040527 ms
  Average    latency    is: 1.084041 ms
  Frame      rate       is: 3584.178005 FPS
```

> **Latency vs FPS 概念**：Latency = 单核单线程推一帧耗时；FPS = 多线程吞吐量。`thread_num=1` 时通过 Latency 推算 FPS = 工具测出 FPS；`thread_num>1` 时两者会不一致——多线程下每个线程的单帧 latency 反而比单线程**长**，但总吞吐升高。要写 FPS 数到对外材料，必须同时写 `thread_num` 和 `core_id`。

---

## 3. `profiler.log` / `profiler.csv` 解读

`--profile_path="."` 产出的 `profiler.log` 是 JSON，五个块：

### 3.1 `perf_result` / `running_condition`

整体性能 + 测试条件——和控制台输出一致，留作归档。

### 3.2 `processor_latency`（**最重要**：判断瓶颈在 BPU 还是 CPU）

```json
"processor_latency": {
  "BPU_inference_time_cost": { "avg_time": 0.849, "max_time": 1.328, "min_time": 0.766 },
  "CPU_inference_time_cost": { "avg_time": 0.075, "max_time": 0.382, "min_time": 0.066 }
}
```

读法：
- **CPU_inference_time_cost > BPU_inference_time_cost / 2** → CPU 是瓶颈，跳到 §5 处理 CPU 算子
- BPU >> CPU → BPU 是瓶颈，按 §5 的"BPU 利用率"路径优化模型结构
- 二者都低但总 latency 高 → 看 `task_latency` 的 TaskPendingTime（任务排队）

### 3.3 `model_latency`（每节点耗时）

```json
"model_latency": {
  "BPU_MOBILENET_subgraph_0": { "avg_time": 0.849, ... },
  "Dequantize_fc7_1_HzDequantize": { "avg_time": 0.029, ... },
  "MOBILENET_subgraph_0_output_layout_convert": { "avg_time": 0.011, ... },
  "Preprocess": { "avg_time": 0.005, ... },
  "Softmax_prob": { "avg_time": 0.028, ... }
}
```

每节点对应 `hb_perf` 主页面 BIN Model Structure 图中的同名节点。重点关注：

| 节点类型 | 含义 | 处理 |
|---|---|---|
| `BPU_xxx_subgraph_N` | BPU 子图整体耗时 | 大头 → §5 模型结构优化 |
| `Preprocess` | 模型输入数据 padding + layout 转换 | 通常很小（μs 级），过大说明 layout 设置不合理 |
| `xxx_input_layout_convert` | BPU 节点输入 padding + layout | 子图切多 → 出现多个 → 加重耗时 |
| `xxx_output_layout_convert` | BPU 节点输出 去 padding + layout | 同上 |
| `Dequantize_xxx_HzDequantize` | 反量化 | 若在尾部 → 用 `remove_node_type` 删（§5.2）|
| `Softmax_xxx` / `Argmax_xxx` 等 | CPU 算子 | §5 处理 |

### 3.4 `task_latency`

```json
"task_latency": {
  "TaskPendingTime": { "avg_time": 0.021, ... },
  "TaskRunningTime": { "avg_time": 0.983, ... }
}
```

- `TaskPendingTime` = 任务排队耗时（提交后未立即跑）。多线程下显著上升，反映线程数过多导致资源抢占。
- `TaskRunningTime` = 实际执行耗时（含 DNN 框架开销）。

如果调高 `thread_num` 之后 FPS 不再增长但 `TaskPendingTime` 暴涨 → 线程数已超过 BPU 实际吞吐能力，**降回去**。

---

## 4. yaml 性能参数清单

完整字段语义见 `yaml-reference.md` §4 `compiler_parameters`；这里只列**性能视角**的关键值与踩坑点。

| 字段 | Model Zoo 默认 | 不改的代价 | 建议 |
|---|---|---|---|
| `compile_mode` | `'latency'` | — | 性能优先**保持 `latency`**；DDR 带宽紧张才考虑 `bandwidth` 或 `balance`（需配 `balance_factor`）|
| `optimize_level` | `'O3'`（必须改！默认 `'O0'`）| **拿不到正常性能** | **生产 / 性能评测必须 `O3`**；调试期可降到 `O0`/`O1` 加快编译 |
| `debug` | `True` | `hb_perf` 拿不到 Layer Details | **保持 `True`**；只增 bin 元数据，不影响推理 |
| `max_time_per_fc` | `0` | — | 仅板端多模型抢占场景才填（单位 μs，取 `1000-4294967295`）|
| `jobs` | `2` | 编译变慢 | 仅影响编译速度，按机器核心数调 |
| `layer_out_dump`（`model_parameters`）| `False` | **每个卷积加反量化节点，显著降速** | **生产必须 `False`**——这是调试用的 |

**最常踩两个**：
1. `optimize_level` 没改成 `O3`——拿到的 `.bin` 性能数据全偏低。
2. `layer_out_dump: True` 留在生产 yaml——卷积后插反量化，hb_perf 看着每层都有耗时，板端实测也变慢。

### 4.1 优化案例

调优前后只改两个字段，往往就能拿到合理性能。如果改完 `optimize_level: O3` + `layer_out_dump: False` 后 `BPU_inference_time_cost` 仍然偏高，再进 §5。

---

## 5. 性能调优决策树

按顺序从上到下尝试：

```
hrt_model_exec perf 实测 latency / FPS 不达标
    │
    ├── 1. 检查 yaml（§4 清单）
    │     · optimize_level 是否 O3
    │     · layer_out_dump 是否 False
    │     · compile_mode 是否 latency
    │     重编一次 hb_mapper makertbin → 再测
    │
    ├── 2. profiler.log 看瓶颈
    │     CPU_inference_time_cost 高 → 走第 3 步
    │     BPU_inference_time_cost 高 → 走第 4 步
    │     TaskPendingTime 高 → 降 thread_num
    │
    ├── 3. CPU 算子处理（瓶颈在 CPU）
    │     a. 查"工具链算子支持约束列表"看能否 BPU 化
    │     b. 算子参数超出约束 → 改浮点模型回到约束内（hb_mapper checker 验证）
    │     c. 算子根本不支持 BPU：
    │          · CPU 节点在模型中部 → 改模型 / 算子替换 / 改 axis 等参数
    │          · CPU 节点在模型首尾（典型 Quantize/Dequantize）→ §5.2 删除
    │
    ├── 4. BPU 利用率低（瓶颈在 BPU）
    │     · BIN Model Structure 图中是否子图被切碎？合并子图
    │     · 模型 BPU 段输入输出维度过大 → 减小（如分割模型 Argmax 合入，Channel ≤ 64）
    │     · 非卷积算子占比高 → 重新设计模型（卷积为主）
    │
    └── 5. 精度-速度权衡（accuracy-tuning.md 的代价）
          主导算子批量 int16（accuracy-tuning.md §4）→ 体积 2x、推理慢 30-50%
          node_info int16 节点 → 累计 5-10 个开始明显
          'ON': 'CPU' 回退 → 仅尾部 1-2 个，超过则性能掉 >30%
```

### 5.1 第一步细节：yaml 重检

```yaml
model_parameters:
  layer_out_dump: False    # 生产必须 False

compiler_parameters:
  compile_mode: 'latency'
  optimize_level: 'O3'     # 默认 O0，必须改
  debug: True              # 保留，调试需要
```

改完重跑 `hb_mapper makertbin` → `hb_perf` → `hrt_model_exec perf`。这一步通常能涨 30%+ 性能。

### 5.2 删除首尾 Quantize/Dequantize

模型首尾的反量化节点常常占 model_latency 的 5-15%，且**通常可以直接搬到应用层**。两种删法：

**A. 重编时删（推荐）**——yaml `model_parameters` 加：

```yaml
model_parameters:
  remove_node_type: "Quantize; Dequantize"
```

**B. 对已有 bin 模型直接修改**（不重编）：

```bash
hb_model_modifier x.bin -a Quantize -a Dequantize
```

**C. 非首尾相连的反量化节点**（中间被切碎的子图边界）：

1. 先 `hb_perf` 拿结构图，看准要删的节点名
2. `hb_model_modifier x.bin` 看当前可删节点列表
3. `hb_model_modifier x.bin -r <node_name>` 自上而下删 Quantize、自下而上删 Dequantize
4. 每删一个节点后重新跑 `hb_model_modifier x_modified.bin` 看新一轮可删列表

> 删完一定要 `hb_verifier` 跑一遍精度（见 `accuracy.md`），删错节点会让 cosine 显著下降。

### 5.3 BPU 利用率优化（模型结构层面）

- BPU 加速核心是**卷积**。非卷积算子越多，BPU 利用率越低。
- BPU 段输入输出维度大 → 量化/反量化耗时 + DDR 带宽压力都涨。
- 典型优化：分割模型把 Argmax 合入模型尾部。**条件**：
  - Caffe Softmax 默认 `axis=1`，ArgMax 默认 `axis=0`——替换时**必须保持 axis 一致**。
  - Argmax Channel **≤ 64**，否则只能在 CPU 上跑。

这一层调整通常意味着改训练模型（不止改 yaml），代价高，作为最后兜底。

---

## 6. 精度-速度权衡

`accuracy-tuning.md` 的几个手段都有性能代价：

| 手段（来源 accuracy-tuning.md）| 精度提升 | 性能 / 体积代价 | 何时用 |
|---|---|---|---|
| `calibration_type: mix` / `kl` / `max` | +1~3% | 编译耗时略增，运行无影响 | **首选**，无运行代价 |
| `node_info` 个别 int16 节点 | 0.5~2% | 5~10 个节点内基本无感；超过开始明显 | 中间敏感节点 |
| `node_info` `'ON': 'CPU'` 回退 | 0.5~2% | **打断 BPU 子图，性能掉 10-30%** | **仅尾部 1-2 个**算子 |
| 主导算子批量 int16（`optimization: set_{NodeKind}_input_int16,set_{NodeKind}_output_int16,...`）| +2~5% | **bin 体积 2x、推理慢 30-50%** | 模型整体敏感（超过 10 个节点）|
| `input_type_rt: featuremap` | 修 nv12 / yuv 转换误差 | 板端预处理责任推回应用层，实时性差 | 仅诊断和最后兜底 |

**决策原则**：

- 速度优先 + 精度够用：保留 PTQ 默认 int8，只调 `calibration_type`，CPU 回退不超过 1 个尾部算子。
- 精度优先 + 速度可妥协：先按主导算子类型批量 int16（accuracy-tuning.md §4），再上 QAT。
- 速度精度都要：先模型结构层面优化（删 CPU 算子、Argmax 合并、减维度），再回精度调优。

如果走完 `accuracy-tuning.md` 决策树后性能已经掉到不可接受，**回退一步**——先做模型结构优化（§5.3）或换模型，比硬抠 PTQ 精度旋钮更划算。

---

## 7. 交叉引用

| 想做 | 看哪里 |
|---|---|
| `compiler_parameters` 字段全集（含 `core_num`、`balance_factor` 等不常用项）| `yaml-reference.md` §4 |
| `remove_node_type` / `layer_out_dump` / `debug_mode` 等 `model_parameters` 字段 | `yaml-reference.md` §1 |
| 测精度（cosine 阈值、`hb_verifier`、ONNX 对比）| `accuracy.md` |
| 调精度（决策树、`calibration_type`、`node_info`、主导算子批量 int16、featuremap 兜底）| `accuracy-tuning.md` |
| 哪些算子能进 BPU（约束列表）| 官方 RST `appendix/supported_op_list` |
| `hb_mapper checker` 验证浮点模型 | `troubleshooting.md` |
| `hb_model_modifier` 完整参数 / 报错 | `troubleshooting.md` |
| 板端 hrt_model_exec 部署（环境、依赖、跨机拷贝）| 官方 RST `runtime/source/quick_start/env_install` |
| OE 1.2.8 docker 环境、`hb_mapper` 安装 | `setup.md` |
