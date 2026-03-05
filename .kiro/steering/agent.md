## 项目规范

### 文档管理
- 未经允许的情况下不要创建任何文档
- 后端文档在 backend/docs/ 里，做任务之前先看文档
- 临时脚本统统放到 backend/scripts/dev 目录

### 代码质量
- 提交代码前必须运行 `make check` 确保代码质量
- 使用 `make format` 格式化代码（ruff format + import sorting）
- 使用 `make lint` 检查代码规范（ruff）
- 使用 `make type-check` 进行类型检查（mypy）
- 已配置 pre-commit 钩子，commit 时会自动检查

### 开发工作流
1. 安装开发依赖：`make dev-install`
2. 安装 pre-commit 钩子：`make pre-commit-install`
3. 开发代码
4. 格式化代码：`make format`
5. 运行检查：`make check`
6. 提交代码：git commit（会自动运行 pre-commit）

### 代码规范
- 行长度：100 字符
- Python 版本：3.12+
- 使用 ruff format 格式化（替代 black）
- 使用 ruff 排序导入（替代 isort）
- 遵循 ruff 的 linting 规则
- 类型提示：强制要求（所有函数必须有类型注解）

### 测试规范
测试的主要目的是让 agent 验证代码正确性，重点维护 E2E 测试。

#### 测试原则
- **重点维护 E2E 测试**：验证完整的用户流程和 API 端点
- **不测试显而易见的逻辑**：简单的 getter/setter、数据转换、配置读取等
- **避免过度测试**：不要为每个函数都写测试，只测关键路径
- 测试要简单直接，易于维护
- 每个测试函数只验证一个场景

#### 什么需要测试
- API 端点的完整请求响应流程（E2E）
- 核心业务流程的端到端执行
- 关键错误处理场景（空输入、无效输入）
- 复杂的业务逻辑和算法

#### 什么不需要测试
- 显而易见的逻辑（简单赋值、返回值、格式化）
- 框架本身的功能（FastAPI、LangChain、Pydantic）
- 配置加载和环境变量读取
- 日志记录函数
- 简单的数据模型和 schema
- 工具函数的每个边界情况（只测主要场景）

#### 测试编写规范
- 使用 pytest 框架
- 测试文件命名：`test_*.py`（如 `test_api.py`）
- 优先写 E2E 测试，放在 `test_api.py` 或 `test_e2e.py`
- 使用类型注解：`-> None`
- 使用 docstring 简要说明测试目的
- 使用 `conftest.py` 定义共享的 fixtures 和工具函数

#### 运行测试
- 运行所有测试：`make test` 或 `pytest`
- 运行单个文件：`pytest tests/test_api.py`
- 测试应该快速执行