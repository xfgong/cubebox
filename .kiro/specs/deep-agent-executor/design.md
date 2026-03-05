# DeepAgentExecutor 系统设计文档 (简化版)

## 概述

DeepAgentExecutor 是一个基于 DeepAgents 框架的 AI 智能体执行系统的 MVP 实现。该系统提供了一个简单的 API 端点，接收用户输入，通过 DeepAgent 处理，并以流式格式返回结果。

**设计目标**：
- 最小化 API 设计（仅一个输入参数）
- 直接创建 DeepAgent 实例（无配置管理）
- 支持流式输出（Server-Sent Events）
- 集成现有的 LLM 工厂

**技术栈**：
- 框架：FastAPI + LangChain + DeepAgents
- 配置：Dynaconf (YAML 配置)
- 日志：Python logging
- 测试：pytest + httpx
- 流式输出：Server-Sent Events (SSE)

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                  FastAPI 应用                           │
│              (API 路由 & 请求处理)                      │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────▼────────────────────────┐
        │   POST /api/v1/agents/run       │
        │   (流式 Agent 执行端点)         │
        │   输入: { "input": "..." }      │
        └────────┬─────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│         DeepAgentExecutor (核心执行器)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. 创建 DeepAgent 实例                          │   │
│  │ 2. 加载工具列表                                 │   │
│  │ 3. 流式执行任务                                 │   │
│  │ 4. 返回事件流                                   │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴──────────────────────────┐
        │                                   │
┌───────▼──────────────┐          ┌────────▼──────────────┐
│   LLM 工厂           │          │   工具注册表          │
│ (模型创建)           │          │ (工具管理)            │
│                      │          │                       │
│ - 从配置创建 LLM     │          │ - 内置工具            │
│ - 支持多个提供商     │          │ - 示例工具            │
└──────────────────────┘          └───────────────────────┘
        │                                   │
        │                                   │
┌───────▼──────────────────────────────────▼──────────────┐
│              LangChain 组件                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │ - ChatOpenAI / ChatOpenAICompatible              │   │
│  │ - StructuredTool (工具定义)                      │   │
│  │ - Tool Calling (工具调用)                        │   │
│  │ - astream_events (流式事件)                      │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              Server-Sent Events (SSE)                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ - 事件流格式                                     │   │
│  │ - 错误处理                                       │   │
│  │ - 日志记录                                       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 核心模块设计

### 1. DeepAgentExecutor (执行器)

**职责**：
- 创建 DeepAgent 实例
- 加载工具列表
- 流式执行任务
- 返回事件流

**关键方法**：

```python
class DeepAgentExecutor:
    def __init__(self)
    async def stream(input_text: str) -> AsyncIterator[AgentEvent]
    def _create_agent() -> Agent
    def _load_tools() -> list[StructuredTool]
```

**执行流程**：

```
1. 初始化
   ├─ 从 LLM 工厂创建 LLM 实例
   ├─ 加载工具列表
   └─ 创建 DeepAgent 实例

2. 流式执行
   ├─ 调用 agent.astream_events()
   ├─ 迭代事件流
   ├─ 转换为 AgentEvent
   └─ 返回给客户端

3. 事件处理
   ├─ on_llm_start - LLM 开始调用
   ├─ on_llm_end - LLM 结束调用
   ├─ on_tool_start - 工具开始执行
   ├─ on_tool_end - 工具结束执行
   ├─ on_chain_end - 链结束
   └─ error - 错误发生
```

### 2. 工具系统 (Tool System)

**工具注册表**：
- 管理所有可用工具
- 支持工具查询和列表
- 支持工具执行

**示例工具 - 计算器**：

```python
class CalculatorInput(BaseModel):
    expression: str = Field(description="数学表达式，如 '2 + 3 * 4'")

def calculator(expression: str) -> str:
    """执行简单的数学计算"""
    try:
        result = eval(expression)
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {str(e)}"

calculator_tool = StructuredTool.from_function(
    name="calculator",
    description="执行简单的数学计算",
    func=calculator,
    args_schema=CalculatorInput,
)
```

---

## API 设计

### 端点: `POST /api/v1/agents/run`

**请求格式**：

```json
{
  "input": "计算 2 + 3 * 4"
}
```

**响应格式 (Server-Sent Events)**：

流式返回多个事件，每个事件一行，格式为：

```
data: <JSON>

```

**事件类型**：

#### 1. 链开始事件 (chain_start)
```json
{
  "type": "chain_start",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "data": {
    "input": "计算 2 + 3 * 4"
  }
}
```

#### 2. LLM 开始事件 (llm_start)
```json
{
  "type": "llm_start",
  "timestamp": "2024-01-15T10:30:46.456Z",
  "data": {
    "model": "gpt-4",
    "messages": [...]
  }
}
```

#### 3. LLM 结束事件 (llm_end)
```json
{
  "type": "llm_end",
  "timestamp": "2024-01-15T10:30:47.789Z",
  "data": {
    "output": "我需要使用计算器工具来计算这个表达式。",
    "usage": {
      "input_tokens": 50,
      "output_tokens": 20
    }
  }
}
```

#### 4. 工具开始事件 (tool_start)
```json
{
  "type": "tool_start",
  "timestamp": "2024-01-15T10:30:48.012Z",
  "data": {
    "tool_name": "calculator",
    "input": {
      "expression": "2 + 3 * 4"
    }
  }
}
```

#### 5. 工具结束事件 (tool_end)
```json
{
  "type": "tool_end",
  "timestamp": "2024-01-15T10:30:49.345Z",
  "data": {
    "tool_name": "calculator",
    "output": "结果: 14"
  }
}
```

#### 6. 链结束事件 (chain_end)
```json
{
  "type": "chain_end",
  "timestamp": "2024-01-15T10:30:50.678Z",
  "data": {
    "output": "2 + 3 * 4 的结果是 14"
  }
}
```

#### 7. 错误事件 (error)
```json
{
  "type": "error",
  "timestamp": "2024-01-15T10:30:51.901Z",
  "data": {
    "error_code": "EXECUTION_ERROR",
    "message": "执行过程中发生错误",
    "details": "..."
  }
}
```

#### 8. 完成事件 (done)
```json
{
  "type": "done",
  "timestamp": "2024-01-15T10:30:52.234Z"
}
```

---

## 数据模型

### 请求模型

```python
class ExecuteRequest(BaseModel):
    """执行请求"""
    input: str = Field(description="用户输入的问题或任务")
```

### 响应事件模型

```python
class AgentEvent(BaseModel):
    """Agent 事件"""
    type: str  # chain_start, llm_start, llm_end, tool_start, tool_end, chain_end, error, done
    timestamp: str  # ISO 8601 格式
    data: dict[str, Any]  # 事件数据

class ChainStartEvent(AgentEvent):
    """链开始事件"""
    type: Literal["chain_start"]
    data: dict[str, Any]  # { "input": str }

class LLMStartEvent(AgentEvent):
    """LLM 开始事件"""
    type: Literal["llm_start"]
    data: dict[str, Any]  # { "model": str, "messages": list }

class LLMEndEvent(AgentEvent):
    """LLM 结束事件"""
    type: Literal["llm_end"]
    data: dict[str, Any]  # { "output": str, "usage": dict }

class ToolStartEvent(AgentEvent):
    """工具开始事件"""
    type: Literal["tool_start"]
    data: dict[str, Any]  # { "tool_name": str, "input": dict }

class ToolEndEvent(AgentEvent):
    """工具结束事件"""
    type: Literal["tool_end"]
    data: dict[str, Any]  # { "tool_name": str, "output": str }

class ChainEndEvent(AgentEvent):
    """链结束事件"""
    type: Literal["chain_end"]
    data: dict[str, Any]  # { "output": str }

class ErrorEvent(AgentEvent):
    """错误事件"""
    type: Literal["error"]
    data: dict[str, Any]  # { "error_code": str, "message": str, "details": str }

class DoneEvent(AgentEvent):
    """完成事件"""
    type: Literal["done"]
    data: dict[str, Any] = Field(default_factory=dict)
```

---

## 错误处理设计

### 错误类型和代码

| 错误代码 | HTTP 状态 | 说明 |
|---------|---------|------|
| INVALID_CONFIG | 400 | Agent 配置无效 |
| MISSING_FIELD | 400 | 缺少必需字段 |
| MODEL_NOT_FOUND | 400 | 模型不存在 |
| PROVIDER_NOT_FOUND | 400 | 提供商不存在 |
| TOOL_NOT_FOUND | 400 | 工具不存在 |
| TOOL_EXECUTION_ERROR | 500 | 工具执行失败 |
| AGENT_EXECUTION_ERROR | 500 | Agent 执行失败 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |

### 错误处理流程

```
1. 捕获异常
   ├─ 验证错误 (ValueError, ValidationError)
   ├─ 工具执行错误 (ToolExecutionError)
   └─ 其他异常 (Exception)

2. 转换为错误响应
   ├─ 确定错误代码
   ├─ 确定 HTTP 状态码
   ├─ 生成错误消息
   └─ 收集错误详情

3. 记录错误
   ├─ 记录错误信息
   ├─ 记录堆栈跟踪
   └─ 记录请求上下文

4. 返回错误响应
   ├─ 返回 HTTP 状态码
   ├─ 返回 JSON 错误响应
   └─ 不暴露敏感信息
```

---

## 日志设计

### 日志级别和事件

| 事件 | 级别 | 内容 |
|------|------|------|
| Agent 创建 | INFO | agent_id, name, model_id |
| 任务开始 | INFO | task_id, agent_id, task_description |
| 工具调用 | DEBUG | tool_name, input_params |
| 工具结果 | DEBUG | tool_name, output |
| 任务完成 | INFO | task_id, duration, result_summary |
| 错误发生 | ERROR | error_code, message, stack_trace |

### 日志格式

```
[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s
```

**示例**：

```
[2024-01-15 10:30:45,123] [cubebox.agents.executor] [INFO] Agent created: id=agent-001, name=Research Agent, model=gpt-4
[2024-01-15 10:30:46,456] [cubebox.agents.executor] [INFO] Task started: task_id=task-001, description=Calculate 2 + 3 * 4
[2024-01-15 10:30:47,789] [cubebox.agents.executor] [DEBUG] Tool called: tool_name=calculator, input={'expression': '2 + 3 * 4'}
[2024-01-15 10:30:48,012] [cubebox.agents.executor] [DEBUG] Tool result: tool_name=calculator, output=结果: 14
[2024-01-15 10:30:49,345] [cubebox.agents.executor] [INFO] Task completed: task_id=task-001, duration=3.222s
```

---

## 项目结构

```
backend/cubebox/
├── agents/
│   ├── __init__.py
│   ├── config.py              # Agent 配置模型 (已存在)
│   ├── executor.py            # DeepAgentExecutor (新建)
│   └── schemas.py             # 请求/响应模型 (新建)
├── tools/
│   ├── __init__.py
│   ├── registry.py            # 工具注册表 (已存在)
│   ├── builtin/
│   │   ├── __init__.py
│   │   └── calculator.py      # 计算器工具 (新建)
│   └── examples/
│       ├── __init__.py
│       └── sample_tools.py    # 示例工具 (新建)
├── api/
│   ├── routes/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   └── agents.py      # Agent API 端点 (新建)
│   │   └── health.py          # 健康检查 (已存在)
│   └── exceptions.py          # API 异常处理 (新建)
└── utils/
    ├── __init__.py
    └── logger.py              # 日志配置 (新建)

tests/
├── __init__.py
├── conftest.py                # pytest 配置 (新建)
├── test_executor.py           # Executor 测试 (新建)
├── test_tools.py              # 工具测试 (新建)
└── test_api.py                # API 测试 (新建)
```

---

## 依赖包

**新增依赖**：
- `deepagents>=0.1.0` - DeepAgents 框架
- `langchain>=0.3.0` - LangChain 核心
- `langchain-core>=0.3.0` - LangChain 核心库
- `langchain-openai>=0.2.0` - OpenAI 集成

**已有依赖**：
- `fastapi` - Web 框架
- `pydantic` - 数据验证
- `dynaconf` - 配置管理
- `pytest` - 测试框架
- `httpx` - HTTP 客户端

---

## 正确性属性

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Valid Config Creates Agent

*For any* valid AgentConfig with all required fields, creating a DeepAgentExecutor should successfully instantiate an Agent without raising an exception.

**Validates: Requirements 1.1, 2.1, 2.2**

### Property 2: Execute Returns Result

*For any* valid Agent and task description, calling execute() should return an ExecutionResult with non-empty output.

**Validates: Requirements 1.2, 1.4**

### Property 3: Invalid Config Raises Error

*For any* AgentConfig with missing required fields, creating a DeepAgentExecutor should raise a ValidationError.

**Validates: Requirements 2.2**

### Property 4: Nonexistent Model Raises ValueError

*For any* AgentConfig with a model_id that doesn't exist in the LLM factory, creating a DeepAgentExecutor should raise a ValueError.

**Validates: Requirements 2.3**

### Property 5: Tools Are Loaded

*For any* Agent created with a list of tool names, the Agent should have all specified tools available for invocation.

**Validates: Requirements 3.1**

### Property 6: Tool Execution Succeeds

*For any* valid tool call with correct parameters, the tool should execute and return a result without raising an exception.

**Validates: Requirements 3.2**

### Property 7: Tool Failure Returns Error

*For any* tool call with invalid parameters, the tool should return an error message instead of raising an exception.

**Validates: Requirements 3.3**

### Property 8: Sample Tool Exists

*For any* ToolRegistry instance, calling list_tools() should return at least one tool (the calculator tool).

**Validates: Requirements 3.4**

### Property 9: API Success Response Format

*For any* successful API request to POST /api/v1/agents/run, the response should have status 200 and contain a "result" field with "output" and "tool_calls".

**Validates: Requirements 4.1, 4.2**

### Property 10: API Bad Request Response

*For any* API request with invalid AgentConfig, the response should have status 400 and contain "error_code" and "message" fields.

**Validates: Requirements 4.3, 5.1, 5.2**

### Property 11: API Model Not Found Response

*For any* API request with a non-existent model_id, the response should have status 400 with error_code "MODEL_NOT_FOUND".

**Validates: Requirements 4.3, 5.3**

### Property 12: API Server Error Response

*For any* API request that triggers an unhandled exception, the response should have status 500 and contain error information.

**Validates: Requirements 4.4**

### Property 13: Error Response Structure

*For any* error response, it should contain "status": "error", "error_code", and "message" fields.

**Validates: Requirements 5.1**

### Property 14: Error Logging Contains Stack Trace

*For any* error that occurs during execution, the error log should contain the error message and stack trace.

**Validates: Requirements 5.4, 6.3**

### Property 15: Agent Execution Logged

*For any* Agent execution, the logs should contain at least one INFO level entry indicating task start or completion.

**Validates: Requirements 6.1**

### Property 16: Tool Call Logged

*For any* tool invocation, the logs should contain a DEBUG level entry with the tool name and input parameters.

**Validates: Requirements 6.2**

### Property 17: E2E Test Framework Supports Agent Creation

*For any* E2E test, the framework should provide utilities to create test Agents and execute tasks.

**Validates: Requirements 7.1**

### Property 18: E2E Test Validates API Response

*For any* E2E test that calls the API, the framework should validate that the response has correct status code and structure.

**Validates: Requirements 7.2**

### Property 19: E2E Test Validates Tool Results

*For any* E2E test that invokes a tool, the framework should validate that the tool result is present and non-empty.

**Validates: Requirements 7.3**

### Property 20: E2E Framework Supports Multiple Tests

*For any* E2E test suite, the framework should support running multiple independent test cases.

**Validates: Requirements 7.4**

---

## 错误处理设计

### 错误处理策略

1. **验证错误** (400 Bad Request)
   - 缺少必需字段
   - 字段类型错误
   - 模型/提供商不存在

2. **执行错误** (500 Internal Server Error)
   - 工具执行失败
   - Agent 执行失败
   - 未预期的异常

3. **错误响应格式**
   - 包含 error_code 和 message
   - 可选的 details 字段
   - 不暴露敏感信息

### 异常处理流程

```python
try:
    # 验证配置
    # 创建 Executor
    # 执行任务
except ValidationError as e:
    # 返回 400 + INVALID_CONFIG
except ValueError as e:
    # 返回 400 + MODEL_NOT_FOUND 或 PROVIDER_NOT_FOUND
except Exception as e:
    # 记录错误和堆栈跟踪
    # 返回 500 + INTERNAL_ERROR
```

---

## 测试策略

### 单元测试

**Executor 测试**：
- 有效配置创建 Agent
- 无效配置抛出异常
- 任务执行返回结果
- 错误处理和异常捕获

**工具测试**：
- 工具注册和查询
- 工具执行成功
- 工具执行失败
- 示例工具可用

**API 测试**：
- 成功请求返回 200
- 无效配置返回 400
- 模型不存在返回 400
- 服务器错误返回 500

### 属性测试

每个正确性属性应该对应一个属性测试，使用 pytest 和 hypothesis 库：

```python
# Feature: deep-agent-executor, Property 1: Valid Config Creates Agent
@given(valid_agent_config())
def test_valid_config_creates_agent(config):
    executor = DeepAgentExecutor(config)
    assert executor.agent is not None

# Feature: deep-agent-executor, Property 2: Execute Returns Result
@given(valid_agent_config(), st.text(min_size=1))
def test_execute_returns_result(config, task):
    executor = DeepAgentExecutor(config)
    result = executor.execute(task)
    assert result.output is not None
    assert len(result.output) > 0
```

### E2E 测试

**测试框架**：
- 创建测试 Agent
- 执行任务
- 验证 API 响应
- 验证工具调用

**测试用例**：
- 简单计算任务
- 多工具调用
- 错误处理
- 日志记录

---

## 实现注意事项

### 1. 与现有系统集成

- 使用现有的 LLM 工厂创建 LLM 实例
- 使用现有的配置系统 (Dynaconf)
- 遵循现有的代码风格和规范

### 2. 工具系统设计

- 工具基于 LangChain StructuredTool
- 支持参数验证 (Pydantic)
- 支持错误处理和日志记录

### 3. API 设计

- 遵循 RESTful 设计原则
- 使用 FastAPI 的依赖注入
- 返回结构化的 JSON 响应

### 4. 日志记录

- 使用 Python logging 模块
- 记录关键事件和错误
- 包含足够的上下文信息

### 5. 错误处理

- 验证所有输入
- 捕获和处理异常
- 返回有意义的错误消息

---

## 后续扩展点

虽然 MVP 范围有限，但设计考虑了以下扩展点：

1. **MCP 支持** - 集成 Model Context Protocol
2. **Skills 系统** - 支持复杂工作流
3. **Sandbox 集成** - 代码执行能力
4. **记忆系统** - 长期和短期记忆
5. **任务队列** - 异步任务执行 (Celery)
6. **数据库** - 持久化任务和结果

