# Bilibili 硬核会员答题 Benchmark 收集工具

自动收集 Bilibili 硬核会员答题数据，生成 LLM Benchmark 数据集。

## ✨ 特性

- 🔄 **渐进式数据收集**：多次运行累积数据，支持断点续传
- 🎯 **智能答题策略**：已知答案时故意选错，避免通过 60 分
- 📊 **完整数据跟踪**：记录每个选项的状态（正确/错误/未知）
- 🤗 **HuggingFace 兼容**：导出为标准的 datasets 格式
- 🏗️ **专业架构**：清晰的分层设计，易于维护和扩展

## 🚀 快速开始

**要求**：Python 3.10+（推荐 3.11 ~ 3.14）

### 1. 安装依赖

```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

### 2. 配置

创建 `.env` 文件：

```env
# OpenAI 兼容 API 配置
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_API_KEY=your_api_key_here

# 答题配置
MAX_QUESTIONS=100
SAFETY_THRESHOLD=55

# 数据配置
BENCHMARK_VERSION=v1
```

### 3. 运行

#### 答题模式（收集数据）

```bash
uv run python -m bili-hardcore-benchmark.main
```

程序会：
1. 显示二维码，扫码登录 B站
2. 验证用户等级（需 6 级）
3. 自动答题并收集数据
4. 实时保存到 `benchmark_data/questions_raw.json`

**可多次运行**，每次运行都会累积更多题目数据。

#### 导出模式（生成 HuggingFace 格式）

```bash
uv run python -m bili-hardcore-benchmark.export
```

导出完整题目（已知正确答案）为：
- `benchmark_data/benchmark_v1/` - HuggingFace Arrow 格式
- `benchmark_data/benchmark_v1.jsonl` - JSONL 格式

#### 可视化模式（查看收集进度）

直接在浏览器中打开 `benchmark_data/dashboard.html`，它会自动读取同目录下的 `questions_raw.json` 并生成交互式仪表盘。

仪表盘功能包括：
- 显示每道题目的选项状态（正确/错误/未知）
- 按分区分组展示热力图
- 包含分区概览、完成情况统计等
- 支持交互式操作（缩放、悬停查看详情等）

## 📁 项目架构

```
bili-hardcore-benchmark/
├── application/              # 应用层：业务逻辑
│   ├── models/              # 数据模型（Question, Benchmark）
│   └── services/            # 业务服务（答题、收集、导出）
├── infrastructure/          # 基础设施层：技术实现
│   ├── bilibili/           # B站 API 客户端（基于 httpx）
│   ├── ai/                 # AI 服务（OpenAI 兼容）
│   ├── persistence/        # 数据持久化和导出
│   └── config/             # 配置管理（Pydantic Settings）
├── common/                  # 公共组件
│   ├── exceptions.py       # 异常体系
│   ├── logging.py          # 日志配置
│   └── types.py            # 类型定义
├── container.py            # 依赖注入容器
├── main.py                 # 答题模式入口
└── export.py               # 导出模式入口
```

### 设计原则

- **两层架构**：应用层（业务逻辑）+ 基础设施层（技术实现）
- **依赖注入**：通过容器管理所有依赖关系
- **类型安全**：全项目类型注解，支持 mypy strict 模式
- **渐进式重构**：新架构与旧代码并存，平滑迁移

## 📊 数据格式

### 中间格式（`questions_raw.json`）

存储所有题目的详细状态：

```json
{
  "version": "1.0",
  "updated_at": "2024-01-15T10:30:00",
  "questions": {
    "12345": {
      "id": "12345",
      "question": "以下哪个不是编程语言？",
      "choices": ["Python", "Java", "HTML", "C++"],
      "correct_answer": 2,
      "attempts": 3,
      "last_attempt": "2024-01-15T10:25:00"
    },
    "67890": {
      "id": "67890",
      "question": "1+1等于多少？",
      "choices": ["1", "2", "3", "4"],
      "wrong_answers": [0, 2],
      "attempts": 2
    }
  }
}
```

**字段说明**：
- `correct_answer`: 正确答案索引（0-based）。一旦设置，题目即完整
- `wrong_answers`: 已知错误答案列表（仅在正确答案未知时使用）
- 单选题逻辑：`correct_answer` 存在时，其他选项自动为错误

### HuggingFace 格式

导出后的标准格式（只包含完整题目）：

```json
{
  "id": "12345",
  "question": "以下哪个不是编程语言？",
  "choices": ["Python", "Java", "HTML", "C++"],
  "answer": 2,
  "category": "computer_science"
}
```

## 🔧 使用数据集

### 加载数据

```python
from datasets import load_dataset, load_from_disk

# 方法1: 加载 Arrow 格式（推荐，速度快）
dataset = load_from_disk("benchmark_data/benchmark_v1")

# 方法2: 加载 JSONL 格式（兼容性好，易分享）
dataset = load_dataset("json", data_files="benchmark_data/benchmark_v1.jsonl")

print(f"数据集大小: {len(dataset)}")
print(f"第一个样本: {dataset[0]}")
```

### 评估模型

```python
# 评估模型
correct = 0
for item in dataset:
    # 使用你的模型预测
    predicted = your_model.predict(item['question'], item['choices'])
    if predicted == item['answer']:
        correct += 1

accuracy = correct / len(dataset) * 100
print(f"准确率: {accuracy:.2f}%")
```

## 🎯 智能答题策略

1. **已完整题目**（`correct_answer` 已知）：
   - 随机选择错误答案（避免通过 60 分）
   - 不调用 AI（节省成本）

2. **部分已知题目**（有 `wrong_answers`）：
   - 从未尝试的选项中随机选择
   - 或使用 AI 在剩余选项中判断

3. **完全未知题目**：
   - 使用 AI 判断

## 🛠️ 开发

### 安装开发依赖

```bash
uv sync --extra dev
```

### 代码质量检查

```bash
# 类型检查
uv run mypy bili-hardcore-benchmark

# 代码格式化
uv run black bili-hardcore-benchmark

# Linting
uv run ruff check bili-hardcore-benchmark
```

## 📝 License

MIT License

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！
