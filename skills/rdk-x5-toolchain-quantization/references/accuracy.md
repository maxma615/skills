# 精度评估

> **何时读**：想验证量化精度是否达标 / 不知道 cosine 阈值合理范围 / 想用 hb_verifier 找首个掉点算子。
>
> **来源**：
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_usage/accuracy_evaluation.rst.txt`
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_tool/hb_verifier.rst.txt`
> - `artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_infer.rst.txt`

## 1. 评估方法对比

PTQ 量化后地平线工具链提供多种精度验证手段，从轻到重依次为：单张 cosine 相似度、`hb_mapper infer` 单输入完整推理、`hb_verifier` 逐层比对、再到端到端任务 metric。

| 方法 | 输入 | 输出 | 何时用 |
| --- | --- | --- | --- |
| 逐张 cosine | 浮点 ONNX vs 定点 ONNX（`*_quantized_model.onnx`） | 单张相似度（标量） | 快速 sanity check，调参 / CI 流水线轻量验证 |
| `hb_mapper infer` | 定点 ONNX + bin（与 makertbin 同一份 yaml + 一张图） | 推理结果（反量化浮点 `${layername}_float.bin`） | 单输入完整推理，验证编译产物可跑通 |
| `hb_verifier` | `.bin` + `quanti.onnx`（+ 可选输入图片 / 随机 tensor） | 浮点 vs 定点逐层 cosine 与 mismatch 报告 | 找首个掉点的算子、定位量化损失位置 |
| 端到端任务 metric | 完整测试集（图片 + GT） | mAP / Acc / IoU 等任务指标 | 最终验收，量化 vs 浮点的业务精度对齐 |

经验：典型流水线是「逐张 cosine 粗筛 → `hb_verifier` 定位 → 端到端 metric 验收」，仅当中间环节出现可疑掉点时再深入。

## 2. cosine similarity 阈值

cosine 的定义：

```
cosine(a, b) = (a · b) / (||a|| · ||b||)
```

值域 `[-1, 1]`，量化场景下我们关心 `≥ 0.95` 这一档。下表给出按任务类型常用的经验阈值，作为「是否需要进入精度调优」的触发线。

| 任务 | 推荐阈值 | 说明 |
| --- | --- | --- |
| 分类 | ≥ 0.99 | 输出维度 = 类别数，logits 方差小，阈值要求最严 |
| 检测 | ≥ 0.95 | 多个 head（cls + reg + obj），bbox 回归对小误差敏感 |
| 分割 | ≥ 0.95 | per-pixel 输出，逐像素累积误差，同检测 |
| Transformer | ≥ 0.95 | 注意力 softmax 对 outlier 与 LayerNorm 量化敏感 |
| Pose | ≥ 0.97 | 关键点回归，坐标偏差对 PCK 影响显著 |

注意事项：

- cosine 高 ≠ 任务 metric 高，最终仍需用端到端 metric 复核。
- 多输出模型应**逐 output** 看 cosine，而不是把所有输出 flatten 后算一个总值。
- 数据要选**有代表性**的（典型样本 + 边界样本），随机噪声的 cosine 没有参考意义。

## 3. hb_mapper infer 用法

`hb_mapper infer` 用浮点 / 量化 ONNX 进行一次完整推理，并把每层输出落盘为 `${layername}_float.bin`，便于和浮点参考结果做向量比对。

### 命令格式

```bash
hb_mapper infer --config ${config_file} \
                --model-file ${quantized_model_file} \
                --model-type onnx \
                --image-file ${input_node} ${image_file} \
                --input-layout NCHW \
                --output-dir ${quantized_output_dir}
```

关键参数（来自 RST）：

- `-c, --config`：**必须与 `hb_mapper makertbin` 使用的同一份 yaml**，保证预处理（mean/scale/layout/type）一致。
- `--model-file`：可以是 `*_original_float_model.onnx`、`*_optimized_float_model.onnx` 或 `*_quantized_model.onnx`。
- `--model-type`：`caffe` 或 `onnx`。
- `--image-file`：格式为 `${input_node_name} ${image_path}`，多输入模型重复给即可。
- `--input-layout`：`NCHW` 或 `NHWC`，可选；缺省时按模型自身定义。
- `--output-dir`：每层一份 `${layername}_float.bin`（量化模型也会做反量化后再落盘）。

### 校准 `.rgbchw` 示例

如果 yaml 里校准 `cal_data_type` 配置为 `float32`、layout 为 `NCHW`、type 为 `rgb`，那么测试图也应该以 `.rgbchw`（float32, CHW, RGB）的形式喂入：

```bash
hb_mapper infer --config yolo_config.yaml \
                --model-file model_quantized_model.onnx \
                --model-type onnx \
                --image-file images sample_001.rgbchw \
                --input-layout NCHW \
                --output-dir infer_out/
```

### 常见坑

- **layout 不一致**：yaml 里 `input_layout_train=NCHW`，但传入的 `.rgbchw` 实际是 NHWC，会得到全黑或乱码输出。
- **dtype 不匹配**：yaml 声明 `float32` 但实际写盘是 `int8`，`np.fromfile` 读出来字节数对不上 shape，直接 reshape 报错。
- **shape 必须固定**：RST 明确说明 `hb_mapper infer` 受 onnxruntime 限制，不支持 dynamic shape，也不支持 shape 含 `?` 的模型；仅支持 4D 输入、输出 ≤ 4D 的非 featuremap 模型。
- **预处理重复**：yaml 已经把 mean/scale 融入模型，准备 `--image-file` 时不要再减 mean / 乘 scale。

## 4. hb_verifier 用法

`hb_verifier` 是定位「首个掉点算子」的核心工具：同时跑 quanti.onnx、bin 板端（ARM）、bin x86 模拟器三方，两两比对原始输出，必要时保存所有节点输出做逐层 diff。

### 命令格式

```bash
hb_verifier -m ${quanti_model},${bin_model} \
            -b ${board_ip} \
            -s True \
            -i ${input_img} \
            -c ${digits} \
            -r True \
            -u ${board_username} \
            -p ${board_password}
```

关键参数：

- `-m, --model`：`quanti.onnx,model.bin`，逗号分隔，**顺序固定**。
- `-b, --board-ip`：板端 IP，需 `ping` 通且已经装好 `hrt_tools`。
- `-s, --run-sim`：是否在 x86 用 libdnn 跑 bin 模型，默认 `False`。
- `-i, --input-img`：可以是图片，也可以是 `.bin` 二进制；不指定则用随机 tensor。
- `-c, --compare_digits`：比较小数位数，默认 5 位。
- `-r, --dump-all-nodes-results`：**关键开关**，开启后保存所有节点输出，按节点名匹配做逐层 diff，用于找首个掉点的算子。
- `-u/-p`：板端用户名/密码，未设密码时不要传 `-p`。

### 典型场景

三方比对（quanti.onnx vs ARM vs Sim）：

```bash
hb_verifier -m quanti.onnx,model.bin -b 192.168.1.100 -s True -i sample.jpg
```

逐层 diff（找首个掉点算子）：

```bash
hb_verifier -m quanti.onnx,model.bin -b 192.168.1.100 -r True -i sample.jpg
```

仅 x86 模拟器对比（无板端）：

```bash
hb_verifier -m quanti.onnx,model.bin -s True -i sample.jpg
```

### 输出示例

通过时（Strict check 全 PASSED）：

```text
Comparison results of original output is model_infer_output_0
raw output 0 and raw output 0 result Strict check PASSED
Quanti.onnx and Arm result Strict check PASSED
```

失败时会输出三段对比（Quanti.onnx VS Arm、Quanti.onnx VS Sim、Arm VS Sim），关键字段：

```text
INFO compare source: Quanti.onnx VS Arm
INFO mismatch result num: 1000
INFO total result num: 1000
INFO mismatch rate: 1.0
INFO relative mismatch ratio: 0.9997149805034536
INFO max abs error: 8.36695
WARNING Quanti.onnx and Arm result Strict check FAILED
```

字段含义：

- `mismatch result num`：不一致结果总数（含 `line_miss` 数量缺失、`line_diff` 差距过大、`line_nan` NaN 三种）。
- `total result num`：输出数据总量。
- `mismatch rate`：不一致比例。
- `relative mismatch ratio`：最大相对误差比例。
- `max abs error`：最大绝对误差。

### 使用前置约束

- 板端必须装好 `hrt_tools`（用 `package/board/install.sh {board_ip}`）；x86 端用 `package/host/host_package/install_host_package.sh`。
- **不要用 `docker attach`** 进入 OE 容器，会导致与板端的 SSH 认证失败，要用 `run_docker.sh` 或 `docker exec -it`。
- 如果用 `hb_model_modifier` 或 yaml 的 `remove_node_type` 删掉了 bin 模型输出前的最后一个非 Dequantize 节点，`hb_verifier` 不再支持该 bin 与 quanti.onnx 的对比。
- 多 batch 模型不支持 binary 输入，建议直接传单 batch 图片或不指定输入（用随机 tensor）。

## 5. cosine 计算脚本（自写）

在 `hb_verifier` 不可用（无板端 / 容器外）、需要批量比对多张图、或想集成进 CI 时，用下面这段最小脚本即可：

```python
# ⚠️ 必须在 Docker 容器内（OE 工具链环境）跑，因为量化 ONNX 含 HzQuantize/
# HzDequantize 等 horizon 自定义算子，裸 onnxruntime 加载会抛
# "Could not find an implementation for the node HzQuantize" 错误。
# 必须用 horizon_tc_ui.HB_ONNXRuntime，它注册了自定义算子实现。

# 注意 import 顺序：HB_ONNXRuntime 必须在 torch 之前 import，否则会有
# protobuf 版本冲突（见 troubleshooting.md §5.2）。
from horizon_tc_ui import HB_ONNXRuntime
import numpy as np

def cosine(a, b):
    a, b = a.flatten(), b.flatten()
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

# hb_mapper makertbin 实际产出的浮点 ONNX 文件名是 <prefix>_original_float_model.onnx
# （已把归一化包进模型，直接喂 raw [0,255] float32 像素即可）
sess_fp = HB_ONNXRuntime(model_file='<prefix>_original_float_model.onnx')
sess_q  = HB_ONNXRuntime(model_file='<prefix>_quantized_model.onnx')

x = np.fromfile('test.rgbchw', dtype=np.float32).reshape(1, 3, 640, 640)
y_fp = sess_fp.run(None, {sess_fp.input_names[0]: x})
y_q  = sess_q.run(None,  {sess_q.input_names[0]: x})

for i, (a, b) in enumerate(zip(y_fp, y_q)):
    print(f'output[{i}]: cosine={cosine(a, b):.4f}')
```

适用场景：

- **hb_verifier 不可用**：开发机不能 SSH 到板端，或工具链未安装好。
- **批量比对**：包一层 `for` 循环遍历目录，统计 cosine 的均值 / min / 分布。
- **集成 CI**：在 GitLab/GitHub Actions 里加阈值校验（如 `assert cosine >= 0.95`），量化后自动 gate。

注意脚本只对比 `<prefix>_original_float_model.onnx` 和 `<prefix>_quantized_model.onnx` 两个 ONNX 产物，**不涉及 bin 模型**，因此无法替代 `hb_verifier` 三方比对；它只是一个轻量补充。

## 6. 何时跳到精度调优

cosine 不达标 → `accuracy-tuning.md`。
