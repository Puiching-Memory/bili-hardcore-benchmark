# 架构说明文档

## 架构概览

Bili-Hardcore-Benchmark 采用**务实的两层架构**，实现高内聚低耦合、简洁清晰的专业级项目结构。

```
┌─────────────────────────────────────┐
│         main.py / export.py         │  程序入口
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│          Container              │  依赖注入
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────┴─────┐   ┌──────┴───────┐
│Application│   │Infrastructure│
│   应用层   │   │  基础设施层   │
└───────────┘   └──────────────┘
```

## 分层设计

### 应用层（Application）

**职责**：包含所有业务逻辑、流程编排和数据模型

```
application/
├── models/                 # 业务模型
│   ├── question.py        # 题目实体（单选题逻辑）
│   └── benchmark.py       # 基准测试聚合根
└── services/              # 业务服务
    ├── quiz_service.py    # 答题核心服务
    ├── benchmark_service.py  # 数据收集服务
    └── export_service.py     # 数据导出服务
```

**关键类**：
- `Question`: 题目实体，封装单选题逻辑
- `Benchmark`: 题目集合管理
- `QuizService`: 智能答题策略实现
- `BenchmarkService`: 数据持久化协调
- `ExportService`: 导出格式转换

### 基础设施层（Infrastructure）

**职责**：处理所有技术实现细节

```
infrastructure/
├── bilibili/              # B站 API 客户端
│   ├── client.py         # 基类（httpx + 签名）
│   ├── auth.py           # 认证 API
│   ├── user.py           # 用户 API
│   └── senior.py         # 答题 API
├── ai/                    # AI 服务
│   ├── provider.py       # AI 提供者基类
│   └── openai_provider.py # OpenAI 实现
├── persistence/           # 数据持久化
│   ├── question_store.py  # JSON 存储
│   └── exporters/         # 导出器
│       ├── huggingface_exporter.py
│       └── jsonl_exporter.py
└── config/                # 配置管理
    └── settings.py        # Pydantic Settings
```

**技术选型**：
- HTTP 客户端：`httpx`（现代、支持异步）
- 配置管理：`pydantic-settings`（类型安全）
- AI 服务：OpenAI 兼容接口
- 数据格式：JSON、JSONL、HuggingFace Arrow

## 核心流程

### 答题流程

```
登录
  ├─ 获取二维码
  ├─ 轮询登录状态
  └─ 提取 access_token 和 csrf
     │
     ├─ 验证用户等级（≥6 级）
     │
     └─ 答题循环
        ├─ 获取题目
        ├─ 获取或创建 Question 对象
        ├─ 检查跳过条件
        │  └─ 已完整题目 + 接近安全阈值 → 跳过（提交错误答案）
        ├─ QuizService.select_answer()
        │  ├─ 已完整：随机选错误答案
        │  ├─ 部分已知：尝试未知选项
        │  └─ 完全未知：AI 预测
        ├─ 提交答案
        ├─ 判断结果（通过分数变化）
        ├─ 推断题目分区（通过分区得分变化）
        └─ BenchmarkService.record_*()
           └─ 使用 correct_answer（而非用户选择的答案）
```

**关键细节**：
- **跳过逻辑**：已完整题目且接近安全阈值时，会提交错误答案以获取下一题，避免分数过高
- **分区检测**：通过比较答题前后的分区得分变化，自动推断题目所属分区
- **答案记录**：使用 `judge_result()` 返回的 `correct_answer`，确保记录的是正确答案而非用户选择

### 导出流程

```
加载中间格式
  ├─ JSONQuestionStore.load()
  └─ Benchmark.from_dict()
     │
     ├─ 过滤完整题目
     │
     └─ ExportService.export_*()
        ├─ HuggingFaceExporter
        └─ JSONLExporter
```

## 数据流

```
┌─────────────┐
│  B站 API    │
└──────┬──────┘
       │ 题目数据
       ↓
┌─────────────┐
│  Question   │ 单选题实体
└──────┬──────┘
       │
       ├─ correct_answer: int?
       └─ wrong_answers: list[int]
       │
       ↓
┌─────────────────┐
│ questions_raw.  │ 中间格式
│     json         │
└──────┬──────────┘
       │ 只导出完整题目
       ↓
┌─────────────────┐
│  HuggingFace    │ 标准格式
│   格式数据集     │
└─────────────────┘
```

## 依赖注入

使用简单的工厂模式通过 `Container` 类管理依赖：

```python
# 创建容器
settings = get_settings()
container = Container(settings)

# 获取服务
quiz_service = container.get_quiz_service()
benchmark_service = container.get_benchmark_service()
```

**优势**：
- 集中管理依赖关系
- 易于测试（可替换实现）
- 避免循环依赖
- 延迟初始化

## 渐进式数据收集

单选题的特殊性：一旦知道正确答案，其他选项自动为错误。

### 状态转换

```
未知题目
  ↓ 尝试选项A（错误）
部分已知（wrong_answers: [0]）
  ↓ 尝试选项B（错误）
部分已知（wrong_answers: [0, 1]）
  ↓ 尝试选项C（正确）
完整题目（correct_answer: 2）
```

### 智能策略

- **避免通过**：
  - 已知正确答案时故意选错，保持分数 < 安全阈值
  - 已完整题目且接近阈值时，跳过并提交错误答案（而非直接跳过）
- **高效探索**：优先尝试未知选项
- **节省成本**：已知答案时不调用 AI
- **自动分区**：通过分数变化自动检测题目分区，无需手动标注

## 代码组织

`main.py` 采用模块化设计，将复杂流程拆分为多个辅助函数：

**登录模块**：
- `qrcode_login()`: 主入口
- `_extract_auth_tokens()`: 提取认证令牌
- `_poll_login_status()`: 轮询登录状态

**答题模块**：
- `run_quiz_session()`: 主循环
- `_fetch_question()`: 获取题目
- `_handle_skip_question()`: 处理跳过逻辑
- `_process_question()`: 处理正常答题流程
- `_get_category_scores()`: 获取分区得分
- `_detect_category()`: 推断题目分区
- `_process_answer_result()`: 处理答题结果

这种设计提高了代码可读性和可维护性，每个函数职责单一、易于测试。

## 扩展性设计

虽然本次重构聚焦架构，但为未来扩展预留了空间：

1. **AI 提供者**：`AIProviderBase` 协议，可扩展支持其他模型
2. **存储后端**：`QuestionStore` 协议，可替换为数据库
3. **导出格式**：独立的 Exporter 类，易于添加新格式
4. **API 客户端**：基于 `BilibiliClient` 基类，统一错误处理

## 测试策略（未实现）

虽然本次重构不包含测试，但架构设计考虑了可测试性：

- **应用层**：纯粹的业务逻辑，易于单元测试
- **基础设施层**：通过 Protocol 定义接口，可用 Mock 替代
- **依赖注入**：便于替换测试桩

## 类型安全

全项目类型注解，支持 mypy strict 模式：

```bash
uv run mypy bili-hardcore --strict
```

使用 Protocol 定义接口：
- `AIProvider`
- `QuestionStore`
- `HuggingFaceExporter`
- `JSONLExporter`

## 性能考虑

1. **延迟初始化**：Container 中的服务按需创建
2. **批量操作**：Benchmark 一次性加载所有题目
3. **原子写入**：使用临时文件 + 重命名保证数据完整性
4. **httpx**：高性能 HTTP 客户端，支持连接池和重试

## 未来改进方向

1. **异步化**：使用 httpx 的异步特性提升并发
2. **数据库**：大规模数据时替换 JSON 为数据库
3. **Web 界面**：基于 FastAPI 提供 Web 管理界面
4. **分布式**：支持多账号并发答题
5. **测试覆盖**：添加单元测试和集成测试

