# Bilibili Hardcore Benchmark

自动收集 Bilibili 硬核会员答题数据并生成 LLM 评估数据集。

## 评估结果 (v1)

<p align="center">
  <img src="assets/radar_distribution.svg" width="100%" />
</p>
<p align="center">
  <img src="assets/overall_accuracy.svg" width="100%" />
</p>
<p align="center">
  <img src="assets/category_comparison.svg" width="100%" />
</p>
<p align="center">
  <img src="assets/detailed_heatmap.svg" width="100%" />
</p>

## 功能特性

- **渐进式收集**：支持断点续传，多次运行可累积数据。
- **智能策略**：已知答案时自动选错以规避 60 分及格线，确保持续收集。
- **完整跟踪**：记录选项的正确、错误及未知状态。
- **标准导出**：支持导出为 HuggingFace datasets 格式（Arrow/JSONL）。

## 快速开始

**环境要求**：Python 3.10+, [uv](https://github.com/astral-sh/uv)

```bash
# 初始化
git submodule update --init --recursive
uv sync --extra cpu  # 或 --extra cuda
```

**配置**：创建 `.env` 文件

```env
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_API_KEY=your_api_key_here
```

**运行**：

```bash
uv run python -m bili-hardcore-benchmark.main    # 收集数据
uv run python -m bili-hardcore-benchmark.export  # 导出数据集
```

## 数据说明

- **原始数据**：`benchmark_data/questions_raw.json` 记录题目及选项状态。
- **导出数据**：包含 `id`, `question`, `choices`, `answer`, `category` 字段。
- **加载示例**：
  ```python
  from datasets import load_from_disk
  dataset = load_from_disk("benchmark_data/benchmark_v1")
  ```

## 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md)：项目架构
- [DEVELOPER.md](DEVELOPER.md)：开发指南
- [LICENSE](LICENSE)：GPL-3.0 开源协议

## 致谢

- [bili-hardcore](https://github.com/Karben233/bili-hardcore) - 核心答题逻辑参考
