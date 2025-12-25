# 开发者文档

本文档面向项目开发者和贡献者，包含项目架构、开发环境设置、代码规范等内容。

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

详细的架构说明请参考 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 🚀 开发环境设置

### 安装开发依赖

```bash
# 安装开发依赖（包含 CPU 版本的 PyTorch）
uv sync --extra dev --extra cpu

# 或安装开发依赖（包含 CUDA 版本的 PyTorch，需要先安装 PyTorch）
uv pip install --index-url https://download.pytorch.org/whl/cu126 torch torchvision torchaudio
uv sync --extra dev --extra cuda
```

### 初始化子模块

项目使用 `lm-evaluation-harness` 作为 Git 子模块，需要先初始化：

```bash
git submodule update --init --recursive
```

## 🔍 代码质量检查

### 类型检查

```bash
# 运行 mypy 类型检查
uv run mypy bili-hardcore-benchmark
```

项目使用 mypy strict 模式，所有代码必须通过类型检查。

### 代码格式化

```bash
# 使用 black 格式化代码
uv run black bili-hardcore-benchmark

# 检查代码格式（不修改）
uv run black --check bili-hardcore-benchmark
```

### Linting

```bash
# 运行 ruff 检查
uv run ruff check bili-hardcore-benchmark

# 自动修复可修复的问题
uv run ruff check --fix bili-hardcore-benchmark
```

### 运行所有检查

```bash
# 类型检查
uv run mypy bili-hardcore-benchmark

# 代码格式化检查
uv run black --check bili-hardcore-benchmark

# Linting
uv run ruff check bili-hardcore-benchmark
```

## 📦 项目依赖管理

### 依赖结构

项目使用 `uv` 作为包管理器，依赖定义在 `pyproject.toml` 中：

- **基础依赖**：所有运行时必需的包
- **可选依赖组**：
  - `dev`: 开发工具（black, ruff, mypy）
  - `cuda`: CUDA 版本的 PyTorch（>= 2.9, < 3.0）
  - `cpu`: CPU 版本的 PyTorch（>= 2.9, < 3.0）

### 本地依赖

项目使用 `lm-evaluation-harness` 作为 Git 子模块（位于 `3rd/lm-evaluation-harness`），通过 `[tool.uv.sources]` 配置为本地路径依赖：

```toml
[tool.uv.sources]
lm_eval = { path = "3rd/lm-evaluation-harness" }
```

这意味着：
- `lm_eval` 包从本地路径安装，而不是从 PyPI
- 修改 `3rd/lm-evaluation-harness` 中的代码会直接影响项目
- 更新子模块后需要重新运行 `uv sync`

### 更新依赖

```bash
# 更新所有依赖到最新兼容版本
uv sync --upgrade

# 更新特定依赖
uv sync --upgrade-package <package-name>
```

## 🧪 测试

（如果项目有测试，在这里添加测试说明）

## 📝 代码规范

### 类型注解

- 所有函数参数和返回值必须有类型注解
- 使用 `typing` 模块的类型（如 `Optional`, `List`, `Dict`）
- 支持 mypy strict 模式检查

### 代码风格

- 使用 black 格式化（行长度 100）
- 遵循 PEP 8 规范
- 使用 ruff 进行 linting

### 文档字符串

- 公共函数和类必须有文档字符串
- 使用 Google 风格的文档字符串

## 🔄 工作流程

### 提交代码

1. 创建功能分支
2. 编写代码并确保通过所有检查
3. 提交 Pull Request

### Pull Request 检查清单

- [ ] 代码通过 mypy 类型检查
- [ ] 代码通过 black 格式化检查
- [ ] 代码通过 ruff linting 检查
- [ ] 添加了必要的测试（如果有）
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确

## 🐛 调试

### 日志

项目使用 `loguru` 进行日志记录，日志配置在 `bili-hardcore-benchmark/common/logging.py` 中。

### 常见问题

1. **子模块未初始化**
   ```bash
   git submodule update --init --recursive
   ```

2. **依赖安装失败**
   ```bash
   # 清理并重新安装
   rm -rf .venv uv.lock
   uv sync
   ```

3. **类型检查失败**
   - 确保所有函数都有类型注解
   - 检查是否有未导入的类型

## 📚 相关文档

- [README.md](README.md) - 用户文档
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构详细说明

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

在提交 PR 之前，请确保：
1. 代码符合项目规范
2. 所有检查都通过
3. 添加了必要的文档
4. 提交信息清晰明确

## 📝 License

GNU General Public License v3.0

详见 [LICENSE](LICENSE) 文件。

