# OE v1.2.8 环境安装

> **何时读**：首次安装 OE 工具链；Docker 拉取失败或 SDK 解压报错；需要离线包或官方资源 URL。
>
> **来源**：
> - 系统要求 / 镜像名命名规范：`artifacts/oe_x5_v1.2.8_doc/cn/_sources/oe_mapper/source/env_install/env_deploy.rst.txt`
> - 部分 Aliyun OSS 下载链接 / `registry.d-robotics.cc` 凭据：D-Robotics 公开交付物料（不在 RST 中，但 URL 与凭据来自地瓜机器人官方交付渠道，可直接复用）
>
> 本文只覆盖**安装 + 启动**。yaml 字段见 `yaml-reference.md`，校准数据见 `calibration.md`，运行期报错见 `troubleshooting.md`。

---

## 1. 资源清单

OE 1.2.8 的 Docker 镜像有 **2 个发布渠道**，任选其一：

| 渠道 | 镜像名 | 拉取方式 | 来源 |
|---|---|---|---|
| **D-Robotics 私有 registry**（首推，速度快） | `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8` | 需先 `docker login`（凭据见下） | D-Robotics 交付渠道 |
| **Docker Hub**（备选，无需登录） | `openexplorer/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8` | `docker pull` 即可 | RST `env_deploy.rst.txt` L88-94 |
| **离线 tar.gz** | 同 D-Robotics 镜像 | `wget` + `docker load` | D-Robotics OSS |

### SDK（核心工具链）

```bash
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/horizon_x5_open_explorer_v1.2.8-py310_20240926.tar.gz
```

解压后即为 OE 包根目录，内含 `package/host/install.sh`、`samples/`、`run_docker.sh` 等。

### 文档

```bash
# 中文文档
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/x5_doc-v1.2.8-py310-cn.zip
# 英文文档
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/x5_doc-v1.2.8-py310-en.zip

unzip x5_doc-v1.2.8-py310-cn.zip -d oe_x5_v1.2.8_doc/cn
```

解压后用浏览器打开 `index.html` 即可，本 Skill 的 RST 摘录就出自其 `_sources/` 子目录。

### Docker 镜像 — 方式 A：D-Robotics 私有 registry（推荐）

登录官方 registry（**注意凭据必须用单引号包起来，否则 `$deliver-ronly` 会被 bash 解析为变量替换变成空字符串**）：

```bash
docker login -u 'ccr$deliver-ronly' registry.d-robotics.cc -p 'VLaeatrjF9yGf6I44trT74zKhUpZSVlr'
```

拉取 CPU / GPU 镜像（按需二选一或全拉）：

```bash
# CPU 版（PTQ 量化够用，体积小）
docker pull registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8

# GPU 版（QAT 训练或需要 GPU 加速时）
docker pull registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_gpu:v1.2.8
```

### Docker 镜像 — 方式 B：Docker Hub（备选，无需登录）

RST `env_deploy.rst.txt` 描述的官方公开渠道：

```bash
docker pull openexplorer/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8
docker pull openexplorer/ai_toolchain_ubuntu_20_x5_gpu:v1.2.8
```

两个渠道的镜像内容一致，区别只在拉取速度（私有 registry 国内更快）。

### 离线 Docker 包（无法访问 registry 时用）

```bash
# CPU
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/docker_openexplorer_ubuntu_20_x5_cpu_v1.2.8.tar.gz
docker load -i docker_openexplorer_ubuntu_20_x5_cpu_v1.2.8.tar.gz

# GPU
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/docker_openexplorer_ubuntu_20_x5_gpu_v1.2.8.tar.gz
docker load -i docker_openexplorer_ubuntu_20_x5_gpu_v1.2.8.tar.gz
```

`docker images` 中应能看到对应 tag。

### Release Note

```bash
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/release_note_CN.txt
```

发版日志，遇到行为差异先翻这里。

---

## 2. 启动 OE Docker

最小可用启动命令（把当前目录挂进容器）：

```bash
docker run -it --rm \
  -v $(pwd):/open_explorer \
  -w /open_explorer \
  registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8 \
  /bin/bash
```

GPU 版需要追加 `--gpus all --shm-size=15g`，并把镜像换成 `..._gpu:v1.2.8`。

**容器内验证**：

```bash
hb_mapper --version
hb_perf --version
```

两条命令都能正常打印版本号即代表工具链已就绪。也可以执行 `ddk_vcs list` 查看完整组件清单。

> **Tip**：若希望容器退出后不销毁，去掉 `--rm`；若希望后台常驻，加 `-d`，之后用 `docker exec -it <容器ID> /bin/bash` 重新进入。

---

## 3. SDK 离线安装（不用 Docker）

不推荐（污染本地环境，依赖冲突常见），仅在无 Docker 权限的服务器上使用。

```bash
tar -xzvf horizon_x5_open_explorer_v1.2.8-py310_20240926.tar.gz
cd horizon_x5_open_explorer_v1.2.8-py310/package/host
bash install.sh
```

脚本会自检依赖，缺什么会中断并给出修正建议，按提示补齐后重跑即可。安装完成后：

```bash
source ~/.bashrc        # 让 PATH / LD_LIBRARY_PATH 生效
ddk_vcs list            # 验证组件
```

**硬性依赖**（见 RST PTQ 章节）：
- Ubuntu 20.04
- Python 3.10、python3-devel、python3-pip
- gcc / g++ 11.4.0（必要时手动建立 `gcc-11.4.0`、`g++-11.4.0` 软链接）
- graphviz
- torch 1.13.0、torchvision 0.14.0

板端可执行程序还需交叉编译工具 `arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu`。

---

## 4. 验证环境可用

在容器或本地 Python 3.10 环境内，用一个最小 ONNX 跑通 checker：

```python
# tiny_export.py
import torch, torch.nn as nn

class Tiny(nn.Module):
    def __init__(self):
        super().__init__()
        self.c = nn.Conv2d(3, 8, 3, padding=1)
    def forward(self, x):
        return self.c(x)

torch.onnx.export(
    Tiny().eval(),
    torch.randn(1, 3, 224, 224),
    "tiny.onnx",
    input_names=["images"], output_names=["y"],
    opset_version=11,
)
```

```bash
python tiny_export.py
hb_mapper checker --model-type onnx --march bayes-e --model tiny.onnx
```

日志尾部不出现 ERROR，且打印出 BPU/CPU 算子分布表（`Node ON Subgraph Type ...`）即代表 BPU 算子预检通过，整套工具链可用。

---

## 5. 开发机推荐配置（来自 RST）

| 项目 | 要求 |
| --- | --- |
| CPU | I3 及以上，或 E3/E5 同级 |
| 内存 | 16 GB 起步 |
| 系统 | Ubuntu 20.04 |
| GPU（仅 QAT / GPU Docker 需要） | CUDA 11.6，驱动 ≥ 510.39.01（推荐 515.76）；适配卡：3090 / 2080Ti / TITAN V / V100S / A100 |

**Docker 基础环境**：
- Docker 19.03+（推荐 19.03）
- 使用 GPU 镜像时还需安装 NVIDIA Container Toolkit 1.13.1~1.13.5（推荐 1.13.5）
- 把当前用户加入 docker 组：
  ```bash
  sudo groupadd docker
  sudo gpasswd -a ${USER} docker
  sudo service docker restart
  ```

更多 CUDA 与显卡兼容性问题，参考 NVIDIA 官方 CUDA Compatibility 文档。
