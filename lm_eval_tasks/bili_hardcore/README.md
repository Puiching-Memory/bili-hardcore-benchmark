# Bili Hardcore Benchmark

Bilibili 硬核会员答题 Benchmark 数据集，用于评估语言模型在中文知识问答任务上的表现。

## 数据集说明

该数据集包含从 Bilibili 硬核会员答题中收集的单选题，涵盖多个知识领域。

### 数据格式

数据集包含以下字段：
- `id`: 题目ID
- `question`: 问题文本
- `choices`: 选项列表（字符串数组）
- `answer`: 正确答案索引（0-based）
- `category`: 题目分类

## 使用方法

### 1. 导出数据集

首先，使用项目导出功能将数据导出为 HuggingFace 格式：

```bash
uv run python -m bili-hardcore-benchmark.export
```

这将生成 `benchmark_data/benchmark_v1/` 目录，包含按分类导出的子数据集（8个分类，详见下方"分类任务"部分）。

### 2. 运行评估

#### 2.1 使用 SiliconFlow API（推荐）

[SiliconFlow](https://siliconflow.cn/) 提供了 OpenAI 兼容的 API 接口，可以通过 `local-completions` 或 `local-chat-completions` 模型类型使用。

> 📖 **参考文档**: [SiliconFlow 语言模型使用文档](https://docs.siliconflow.cn/cn/userguide/capabilities/text-generation)

**获取 API Key**

1. 访问 [SiliconFlow 控制台](https://cloud.siliconflow.cn/)
2. 注册/登录账号
3. 在 [API Key 管理页面](https://cloud.siliconflow.cn/account/ak) 创建并复制您的 API Key

**设置 API Key**

在 Linux/macOS 中：
```bash
export OPENAI_API_KEY="your_siliconflow_api_key"
```

在 Windows PowerShell 中：
```powershell
$env:OPENAI_API_KEY="your_siliconflow_api_key"
```

**评估所有分类（推荐）**

`bili_hardcore` 任务默认会评估所有8个分类，并计算加权平均准确率（按各分类的题目数量加权）：

```powershell
# 使用 Chat Completions API（推荐，适用于 generate_until 任务类型）
lm_eval --model local-chat-completions `
    --model_args model=Qwen/Qwen3-8B,base_url=https://api.siliconflow.cn/v1/chat/completions,tokenized_requests=False `
    --tasks bili_hardcore `
    --include_path lm_eval_tasks `
    --output_path results/ `
    --apply_chat_template `
    --log_samples

# 启用并发请求以提高速度（可选，推荐）
lm_eval --model local-chat-completions `
    --model_args model=Qwen/Qwen3-8B,base_url=https://api.siliconflow.cn/v1/chat/completions,tokenized_requests=False,num_concurrent=6 `
    --tasks bili_hardcore `
    --include_path lm_eval_tasks `
    --output_path results/ `
    --apply_chat_template `
    --log_samples
```

> ⚠️ **重要**: 使用 `local-chat-completions` 时必须添加 `--apply_chat_template` 标志，用于将文本 prompt 转换为 Chat Completions API 需要的消息格式（list[dict]）。


**评估单个分类**

也可以单独评估某个分类，只需将 `bili_hardcore` 替换为对应的分类任务名称（详见下方"分类任务"部分）：

```powershell
# 示例：评估体育分类
lm_eval --model local-chat-completions `
    --model_args model=Qwen/Qwen3-8B,base_url=https://api.siliconflow.cn/v1/chat/completions,tokenized_requests=False `
    --tasks bili_hardcore_sports `
    --include_path lm_eval_tasks `
    --output_path results/ `
    --apply_chat_template
```

**API 和参数说明**

本 benchmark 使用 `generate_until` 任务类型，模型直接生成答案字母（如 "A"、"B"、"C"、"D"）。推荐使用 Chat Completions API，特别适合 Instruct 模型。

**API 类型选择：**

- ✅ **推荐：Chat Completions API** (`local-chat-completions`)
  - 使用对话式接口，适合指令微调模型（如 `Qwen3-8B`）
  - `base_url`: `https://api.siliconflow.cn/v1/chat/completions`
  
- **可选：Completions API** (`local-completions`)
  - 使用传统文本补全接口，适合基础模型
  - `base_url`: `https://api.siliconflow.cn/v1/completions`

**必需参数：**

- `model`: SiliconFlow 模型名称（格式：`namespace/model_name`），可在 [模型广场](https://siliconflow.cn/models) 查看
- `base_url`: API 完整端点地址（见上方）
- `tokenized_requests`: 设置为 `False`（对于 SiliconFlow API，建议使用字符串格式而非 token 列表）
- `OPENAI_API_KEY`: 可通过环境变量设置，或通过 `--model_args` 中的 `api_key` 参数传递

**可选参数：**

```powershell
# 示例：使用高级参数
lm_eval --model local-chat-completions `
    --model_args model=Qwen/Qwen3-8B,base_url=https://api.siliconflow.cn/v1/chat/completions,tokenized_requests=False,num_concurrent=10,temperature=0.7,max_tokens=4096,top_p=0.9 `
    --tasks bili_hardcore `
    --include_path lm_eval_tasks `
    --output_path results/ `
    --apply_chat_template
```

常用可选参数：
- `num_concurrent` (默认: 1): 并发请求数，建议 5-20 以提高速度
- `temperature` (0.0~2.0): 控制输出随机性
- `max_tokens`: 最大生成 token 数，建议不超过模型上下文长度的 90%
- `top_p` (0.0~1.0): 核采样参数
- `frequency_penalty` (-2.0~2.0): 频率惩罚，抑制重复用词

**注意事项**

1. **API Key**: 确保已设置正确的 SiliconFlow API Key，部分模型可能需要实名认证
2. **apply_chat_template**: 使用 `local-chat-completions` 时**必须**添加 `--apply_chat_template` 标志，用于将文本 prompt 转换为消息格式
3. **参数配置**: 如遇到参数错误，请确保添加 `tokenized_requests=False`
4. **并发请求**: 推荐设置 `num_concurrent=10` 以提高评估速度，如遇到 429 错误（速率限制），请降低并发数
5. **成本**: 使用 API 会产生费用（按输入/输出 tokens 计费），计费公式：`总费用 = (输入tokens × 输入单价) + (输出tokens × 输出单价)`
6. **max_tokens**: 不要设置为模型最大上下文长度，建议留出约 10k tokens 作为输入空间
7. **输出截断**: 如遇到输出截断，检查 `max_tokens` 设置或考虑使用流式输出

**错误处理**

| 错误码 | 常见原因 | 解决方案 |
|--------|---------|---------|
| 400 | 参数格式错误 | 检查参数取值范围，确保 `tokenized_requests=False` |
| 401 | API Key 未设置或无效 | 检查 API Key 是否正确设置 |
| 403 | 权限不足 | 通常需要实名认证，参考报错信息 |
| 429 | 请求频率超限 | 降低 `num_concurrent` 值或实施指数退避重试 |
| 503/504 | 模型过载 | 稍后重试或切换备用节点 |

## 任务配置

### 任务组（默认）

- `bili_hardcore.yaml` - 任务组配置，同时评估所有8个分类
  - 计算每个分类的准确率
  - 计算加权平均准确率（按各分类题目数量加权）

### 分类任务

每个分类都有独立的任务配置文件，可以单独评估。分类列表如下：

| 分类名称  | 任务名称                   | 配置文件                        | 数据目录     |
| --------- | -------------------------- | ------------------------------- | ------------ |
| 体育      | `bili_hardcore_sports`     | `bili_hardcore_sports.yaml`     | `体育/`      |
| 文史      | `bili_hardcore_literature` | `bili_hardcore_literature.yaml` | `文史/`      |
| 知识      | `bili_hardcore_knowledge`  | `bili_hardcore_knowledge.yaml`  | `知识/`      |
| 动画/漫画 | `bili_hardcore_anime`      | `bili_hardcore_anime.yaml`      | `动画_漫画/` |
| 影视      | `bili_hardcore_movie`      | `bili_hardcore_movie.yaml`      | `影视/`      |
| 游戏      | `bili_hardcore_game`       | `bili_hardcore_game.yaml`       | `游戏/`      |
| 音乐      | `bili_hardcore_music`      | `bili_hardcore_music.yaml`      | `音乐/`      |
| 鬼畜      | `bili_hardcore_kichiku`    | `bili_hardcore_kichiku.yaml`    | `鬼畜/`      |

所有任务配置使用以下设置：
- 数据集路径：`benchmark_data/benchmark_v1/{分类名}`（Arrow 格式）
- 测试集：`train` split
- 输出类型：`generate_until`（模型直接生成答案字母，如 "A"、"B"、"C"、"D"）
- 评估指标：准确率 (acc)

## 参考资源

- [SiliconFlow 官方网站](https://siliconflow.cn/)
- [SiliconFlow 语言模型使用文档](https://docs.siliconflow.cn/cn/userguide/capabilities/text-generation)
- [SiliconFlow 模型广场](https://siliconflow.cn/models)
- [SiliconFlow API 文档](https://docs.siliconflow.cn/cn/)
- [lm-evaluation-harness 文档](https://github.com/EleutherAI/lm-evaluation-harness)

