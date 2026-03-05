## 项目规范

### 文档管理
- 未经允许的情况下不要创建任何文档
- 后端文档在 backend/docs/ 里，做任务之前先看文档
- 临时脚本统统放到 backend/scripts/dev 目录

### 代码质量
- 提交代码前必须运行 `make check` 确保代码质量
- 使用 `make format` 格式化代码（black + isort）
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
- 使用 black 格式化
- 使用 isort 排序导入
- 遵循 ruff 的 linting 规则
- 类型提示：强制要求（所有函数必须有类型注解）