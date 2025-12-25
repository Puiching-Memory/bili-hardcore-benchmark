# Bilibili 硬核会员答题 Benchmark 收集工具

自动收集 Bilibili 硬核会员答题数据，生成 LLM Benchmark 数据集。

## ✨ 特性

- 🔄 **渐进式数据收集**：多次运行累积数据，支持断点续传
- 🎯 **智能答题策略**：已知答案时故意选错，避免通过 60 分
- 📊 **完整数据跟踪**：记录每个选项的状态（正确/错误/未知）
- 🤗 **HuggingFace 兼容**：导出为标准的 datasets 格式

## 🚀 快速开始

**前置要求**：Python 3.10+、[uv](https://github.com/astral-sh/uv)、Git

```bash
# 初始化子模块
git submodule update --init --recursive

# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖（CPU 版本）
uv sync --extra cpu

# 或安装 CUDA 版本（需要先安装 PyTorch，支持 CUDA 12.6/12.8/13.0）
uv pip install --index-url https://download.pytorch.org/whl/cu126 torch torchvision torchaudio
uv sync --extra cuda
```

**配置**：创建 `.env` 文件

```env
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_API_KEY=your_api_key_here
MAX_QUESTIONS=100
SAFETY_THRESHOLD=55
BENCHMARK_VERSION=v1
```

**使用**：

```bash
# 收集数据
uv run python -m bili-hardcore-benchmark.main

# 导出数据集
uv run python -m bili-hardcore-benchmark.export

# 查看进度（打开 benchmark_data/dashboard.html）
```

程序会显示二维码登录，验证用户等级（需 6 级），自动答题并保存到 `benchmark_data/questions_raw.json`。**可多次运行**累积数据。导出为 HuggingFace 格式（Arrow 和 JSONL）。

## 📊 数据格式

**中间格式**（`questions_raw.json`）：包含 `correct_answer`（正确答案索引，0-based）和 `wrong_answers`（已知错误答案列表）。

**导出格式**：标准 HuggingFace 格式，包含 `id`、`question`、`choices`、`answer`、`category`。

## 🔧 使用数据集

```python
from datasets import load_dataset, load_from_disk

dataset = load_from_disk("benchmark_data/benchmark_v1")  # Arrow 格式
# 或
dataset = load_dataset("json", data_files="benchmark_data/benchmark_v1.jsonl")  # JSONL 格式
```

## 🎯 智能答题策略

- **已完整题目**：随机选错，不调用 AI
- **部分已知题目**：从未尝试选项中随机选择或使用 AI
- **完全未知题目**：使用 AI 判断

## 🛠️ 开发者文档

查看 [DEVELOPER.md](DEVELOPER.md) 了解项目架构和开发指南。

## 🙏 致谢

- [bili-hardcore](https://github.com/Karben233/bili-hardcore) - B 站硬核会员 AI 自动答题脚本

## 📝 License

GNU General Public License v3.0 - 详见 [LICENSE](LICENSE)
