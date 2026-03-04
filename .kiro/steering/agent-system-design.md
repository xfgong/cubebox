# AI 智能体系统 - 核心架构设计

## 项目概述

基于 DeepAgents 框架的 AI 智能体系统，支持多 Agent 协作、代码执行、记忆管理等核心功能。

**技术栈**：
- Agent 框架：DeepAgents (LangChain 官方 agent harness)
- 底层框架：LangChain + LangGraph
- 后端框架：FastAPI
- 任务队列：Celery
- 数据库：MySQL
- 缓存/消息队列：Redis
- 向量库：Elasticsearch
- 代码沙箱：OpenSandbox (Ali 开源)
- 协议支持：MCP (Model Context Protocol)
- 前端：Next.js

**DeepAgents 核心能力**：
- 内置任务规划 (Planning Tool)
- 文件系统管理 (Filesystem Backend)
- 子 Agent 委托 (Subagent Spawning)
- 长期记忆管理 (Long-term Memory)
- Token 管理和上下文优化

---

## 1. 整体系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
│              (请求路由、认证、速率限制、MCP 支持)            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────────┐  ┌──────▼──────────────┐
│  DeepAgents Core     │  │  Task Scheduler    │
│  (Agent Harness)     │  │  (Celery)          │
│  ┌────────────────┐  │  └──────┬──────────────┘
│  │ Planning Tool  │  │         │
│  │ (任务规划)     │  │         │
│  └────────────────┘  │         │
│  ┌────────────────┐  │         │
│  │ Filesystem     │  │         │
│  │ (上下文管理)   │  │         │
│  └────────────────┘  │         │
│  ┌────────────────┐  │         │
│  │ Subagent Mgr   │  │         │
│  │ (子 Agent)     │  │         │
│  └────────────────┘  │         │
└───────┬──────────────┘         │
        │                        │
        │    ┌────────────────────┘
        │    │
┌───────▼────▼──────────────────────────────────────┐
│         LangGraph Runtime (执行引擎)               │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ LLM Provider │  │ Tool Manager │              │
│  │ (多模型支持) │  │ (工具调用)   │              │
│  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Memory Mgr   │  │ MCP Client   │              │
│  │ (记忆系统)   │  │ (协议支持)   │              │
│  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ OpenSandbox  │  │ Skills Mgr   │              │
│  │ Client       │  │ (技能管理)   │              │
│  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────┘
        │                        │
        │                        │
┌───────▼──────────────┐  ┌──────▼──────────────┐
│ OpenSandbox Server   │  │  MCP Servers        │
│ (代码执行沙箱)       │  │  (外部工具/服务)    │
│  - Docker Runtime    │  │  - Web Search       │
│  - Code Interpreter  │  │  - Database         │
│  - File Operations   │  │  - Custom Tools     │
└──────────────────────┘  └─────────────────────┘
        │
┌───────▼──────────────────────────────────────────┐
│         Data & Storage Layer                      │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   MySQL      │  │  Redis       │             │
│  │ (持久化)     │  │ (缓存/队列)  │             │
│  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ Elasticsearch│  │  File Store  │             │
│  │ (向量/搜索)  │  │ (代码/结果)  │             │
│  └──────────────┘  └──────────────┘             │
└──────────────────────────────────────────────────┘
```

---

## 2. OpenSandbox 集成方案

### 2.1 OpenSandbox 核心特性

| 特性 | 说明 |
|------|------|
| **多语言支持** | Python、JavaScript、Java、C#、Go 等 |
| **统一 API** | 统一的沙箱生命周期和执行 API |
| **灵活运行时** | 支持 Docker 和 Kubernetes |
| **Code Interpreter** | 内置代码解释器 SDK |
| **网络隔离** | Ingress Gateway + Egress 控制 |
| **资源限制** | CPU、内存、磁盘、网络限制 |

### 2.2 架构集成点

```
Agent Execution Engine
        │
        ├─ 需要执行代码
        │
        ▼
OpenSandbox Client (Python SDK)
        │
        ├─ 创建 Sandbox 实例
        ├─ 执行代码/命令
        ├─ 读写文件
        └─ 获取执行结果
        │
        ▼
OpenSandbox Server (FastAPI)
        │
        ├─ 生命周期管理
        ├─ 容器编排
        └─ 资源隔离
        │
        ▼
Docker/Kubernetes Runtime
        │
        └─ 实际执行环境
```

### 2.3 集成流程

```
1. 初始化阶段
   ├─ 启动 OpenSandbox Server
   ├─ 配置 Docker/K8s 运行时
   └─ 初始化 OpenSandbox Client

2. 执行阶段
   ├─ Agent 决定执行代码
   ├─ 调用 OpenSandbox Client
   ├─ 创建临时 Sandbox
   ├─ 执行代码/命令
   ├─ 收集结果 (stdout/stderr/exit_code)
   └─ 销毁 Sandbox

3. 结果处理
   ├─ 保存执行结果到 MySQL
   ├─ 存储日志到 Elasticsearch
   ├─ 更新 Agent 记忆
   └─ 返回给 Agent 继续推理
```

---

## 3. 核心模块设计

### 3.1 DeepAgent 核心模块

```python
# 基于 DeepAgents 的核心类结构
from deepagents import create_deep_agent
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver

# 创建 Deep Agent
agent = create_deep_agent(
    name="research_agent",
    model="gpt-4",  # 或其他支持 tool calling 的模型
    tools=[web_search_tool, code_execution_tool],
    system_prompt="You are a research assistant...",
    # DeepAgents 内置功能
    planning=True,  # 启用任务规划
    filesystem=True,  # 启用文件系统
    subagents=True,  # 启用子 Agent
    memory=MemorySaver(),  # 长期记忆
)

# Agent 配置模型
class AgentConfig(BaseModel):
    id: str
    name: str
    role: str
    description: str
    system_prompt: str
    model: str  # gpt-4, claude-3, etc.
    tools: List[str]  # 工具名称列表
    skills: List[str]  # Skills 列表
    planning_enabled: bool = True
    filesystem_enabled: bool = True
    subagents_enabled: bool = True
    memory_config: Dict[str, Any]
    mcp_servers: List[str] = []  # MCP 服务器列表

# Task 模型
class Task(BaseModel):
    id: str
    agent_id: str
    description: str
    expected_output: str
    input_data: Dict[str, Any]
    status: TaskStatus  # pending/running/completed/failed
    output_data: Optional[Dict[str, Any]]
    plan: Optional[List[str]]  # DeepAgents 生成的计划
    subtasks: List[str] = []  # 子任务 ID
    parent_task_id: Optional[str]  # 父任务 ID

# Agent 执行器
class DeepAgentExecutor:
    def __init__(self, agent_config: AgentConfig):
        self.config = agent_config
        self.agent = self._create_agent()
        
    def _create_agent(self):
        """创建 DeepAgent 实例"""
        tools = self._load_tools()
        return create_deep_agent(
            name=self.config.name,
            model=self.config.model,
            tools=tools,
            system_prompt=self.config.system_prompt,
            planning=self.config.planning_enabled,
            filesystem=self.config.filesystem_enabled,
            subagents=self.config.subagents_enabled,
        )
    
    async def execute(self, task: Task) -> Result:
        """执行任务"""
        result = await self.agent.ainvoke({
            "messages": [{"role": "user", "content": task.description}]
        })
        return result
    
    async def stream(self, task: Task) -> AsyncIterator[Event]:
        """流式执行任务"""
        async for event in self.agent.astream_events({
            "messages": [{"role": "user", "content": task.description}]
        }):
            yield event
```

### 3.2 工具系统 (Tool Manager + MCP)

```python
# 工具基类 (LangChain StructuredTool)
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    """工具输入模型"""
    pass

class ToolRegistry:
    """工具注册表"""
    def __init__(self):
        self._tools: Dict[str, StructuredTool] = {}
        self._mcp_clients: Dict[str, MCPClient] = {}
    
    def register_tool(self, tool: StructuredTool):
        """注册内置工具"""
        self._tools[tool.name] = tool
    
    def register_mcp_server(self, server_name: str, config: Dict):
        """注册 MCP 服务器"""
        client = MCPClient(config)
        self._mcp_clients[server_name] = client
        # 自动注册 MCP 服务器提供的工具
        for tool in client.list_tools():
            self._tools[tool.name] = self._wrap_mcp_tool(tool)
    
    def get_tool(self, name: str) -> StructuredTool:
        return self._tools.get(name)
    
    def list_tools(self) -> List[StructuredTool]:
        return list(self._tools.values())

# 内置工具示例
class WebSearchInput(BaseModel):
    query: str = Field(description="搜索查询")
    max_results: int = Field(default=10, description="最大结果数")

web_search_tool = StructuredTool.from_function(
    name="web_search",
    description="搜索网络信息",
    func=web_search_function,
    args_schema=WebSearchInput,
)

class CodeExecutionInput(BaseModel):
    code: str = Field(description="要执行的代码")
    language: str = Field(description="编程语言")
    timeout: int = Field(default=30, description="超时时间(秒)")

code_execution_tool = StructuredTool.from_function(
    name="code_execution",
    description="在沙箱中执行代码",
    func=execute_code_in_sandbox,
    args_schema=CodeExecutionInput,
)

# MCP 工具包装器
class MCPClient:
    """MCP 协议客户端"""
    def __init__(self, config: Dict):
        self.config = config
        self.client = self._connect()
    
    def _connect(self):
        """连接到 MCP 服务器"""
        # 实现 MCP 连接逻辑
        pass
    
    def list_tools(self) -> List[Dict]:
        """列出 MCP 服务器提供的工具"""
        return self.client.list_tools()
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """调用 MCP 工具"""
        return self.client.call_tool(tool_name, arguments)
```

### 3.3 记忆系统 (DeepAgents Memory)

```python
# DeepAgents 使用 LangGraph 的 Checkpointer 进行记忆管理
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, AIMessage

# 短期记忆 (对话历史)
class ShortTermMemory:
    """基于 LangGraph State 的短期记忆"""
    def __init__(self, checkpointer: MemorySaver):
        self.checkpointer = checkpointer
    
    def add_message(self, thread_id: str, message: HumanMessage | AIMessage):
        """添加消息到对话历史"""
        # LangGraph 自动管理对话历史
        pass
    
    def get_history(self, thread_id: str, limit: int = 10) -> List[Message]:
        """获取对话历史"""
        checkpoint = self.checkpointer.get(thread_id)
        return checkpoint.get("messages", [])[-limit:]

# 长期记忆 (向量数据库)
class LongTermMemory:
    """基于 Elasticsearch 的长期记忆"""
    def __init__(self, es_client: Elasticsearch):
        self.es = es_client
        self.index_name = "agent_memory"
    
    async def store(self, agent_id: str, content: str, metadata: Dict):
        """存储记忆到向量数据库"""
        embedding = await self._embed(content)
        doc = {
            "agent_id": agent_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata,
            "created_at": datetime.now()
        }
        await self.es.index(index=self.index_name, document=doc)
    
    async def search(self, agent_id: str, query: str, top_k: int = 5) -> List[Dict]:
        """搜索相关记忆"""
        query_embedding = await self._embed(query)
        result = await self.es.search(
            index=self.index_name,
            knn={
                "field": "embedding",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": 100,
                "filter": {"term": {"agent_id": agent_id}}
            }
        )
        return [hit["_source"] for hit in result["hits"]["hits"]]
    
    async def _embed(self, text: str) -> List[float]:
        """生成文本嵌入"""
        # 使用 OpenAI embeddings 或其他嵌入模型
        pass

# 记忆管理器
class MemoryManager:
    """统一的记忆管理接口"""
    def __init__(self, short_term: ShortTermMemory, long_term: LongTermMemory):
        self.short_term = short_term
        self.long_term = long_term
    
    async def retrieve_context(self, agent_id: str, thread_id: str, query: str) -> str:
        """检索相关上下文"""
        # 1. 获取短期记忆 (对话历史)
        recent_messages = self.short_term.get_history(thread_id, limit=10)
        
        # 2. 搜索长期记忆 (向量搜索)
        relevant_memories = await self.long_term.search(agent_id, query, top_k=5)
        
        # 3. 组合上下文
        context = self._format_context(recent_messages, relevant_memories)
        return context
```

### 3.4 LLM 集成层 (多模型支持)

```python
# DeepAgents 支持任何 LangChain 兼容的 LLM
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama

# LLM 配置
class LLMConfig(BaseModel):
    provider: str  # openai, anthropic, ollama, etc.
    model: str
    api_key: Optional[str]
    base_url: Optional[str]
    temperature: float = 0.7
    max_tokens: Optional[int]

# LLM 工厂
class LLMFactory:
    @staticmethod
    def create(config: LLMConfig):
        if config.provider == "openai":
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        elif config.provider == "anthropic":
            return ChatAnthropic(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        elif config.provider == "ollama":
            return Ollama(
                model=config.model,
                base_url=config.base_url or "http://localhost:11434",
                temperature=config.temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

# 使用示例
llm = LLMFactory.create(LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
))

agent = create_deep_agent(
    name="my_agent",
    model=llm,  # 传入 LLM 实例
    tools=[...],
)
```

### 3.5 OpenSandbox 集成模块

```python
SandboxExecutor
├── client: OpenSandboxClient
├── execute_code(code: str, language: str) -> ExecutionResult
├── execute_command(command: str) -> ExecutionResult
├── read_file(path: str) -> str
├── write_file(path: str, content: str) -> None

ExecutionResult
├── stdout: str
├── stderr: str
├── exit_code: int
├── duration_ms: int
├── memory_used_mb: float
└── error: Optional[str]

SandboxConfig
├── timeout: timedelta
├── memory_limit: int (MB)
├── cpu_limit: float
├── network_enabled: bool
└── environment: Dict[str, str]
```

---

## 4. 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── factory.py          # DeepAgent 工厂
│   │   ├── executor.py         # Agent 执行器
│   │   ├── registry.py         # Agent 注册表
│   │   └── config.py           # Agent 配置模型
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py         # Tool 注册表
│   │   ├── builtin/
│   │   │   ├── web_search.py
│   │   │   ├── code_execution.py  # 使用 OpenSandbox
│   │   │   ├── file_operations.py
│   │   │   └── data_query.py
│   │   └── mcp/
│   │       ├── __init__.py
│   │       ├── client.py       # MCP 客户端
│   │       └── wrapper.py      # MCP 工具包装器
│   ├── sandbox/
│   │   ├── __init__.py
│   │   ├── executor.py         # OpenSandbox 执行器
│   │   ├── config.py           # Sandbox 配置
│   │   └── models.py           # 执行结果模型
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── short_term.py       # 短期记忆 (LangGraph)
│   │   ├── long_term.py        # 长期记忆 (Elasticsearch)
│   │   └── manager.py          # 记忆管理器
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── factory.py          # LLM 工厂
│   │   └── config.py           # LLM 配置
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── manager.py          # Skills 管理器
│   │   ├── loader.py           # Skills 加载器
│   │   ├── executor.py         # Skills 执行器
│   │   └── models.py           # Skills 数据模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── agents.py       # Agent API
│   │   │   ├── tasks.py        # Task API
│   │   │   ├── skills.py       # Skills API
│   │   │   ├── sandbox.py      # Sandbox API
│   │   │   └── mcp.py          # MCP API
│   │   ├── schemas.py          # Pydantic 模型
│   │   └── dependencies.py     # 依赖注入
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy 模型
│   │   ├── session.py          # 数据库会话
│   │   └── migrations/         # Alembic 迁移
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── celery_tasks.py     # Celery 任务
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # 日志配置
│       └── exceptions.py       # 自定义异常
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_sandbox.py
│   ├── test_memory.py
│   └── test_skills.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md

frontend/
├── app/
│   ├── page.tsx
│   ├── layout.tsx
│   ├── agents/
│   │   └── [id]/page.tsx
│   ├── tasks/
│   │   └── [id]/page.tsx
│   ├── skills/
│   │   └── page.tsx
│   └── api/
├── components/
│   ├── AgentChat.tsx
│   ├── TaskMonitor.tsx
│   ├── ExecutionViewer.tsx
│   ├── SkillsMarketplace.tsx
│   └── MCPServerManager.tsx
├── lib/
│   ├── api.ts
│   └── types.ts
├── package.json
└── next.config.js
```

---

## 5. 数据库设计 (MySQL)

### 5.1 核心表结构

```sql
-- Agents 表
CREATE TABLE agents (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    role VARCHAR(255),
    system_prompt TEXT,
    tools JSON,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Tasks 表
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    description TEXT NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    input_data JSON,
    output_data JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Executions 表 (代码执行记录)
CREATE TABLE executions (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    code TEXT,
    language VARCHAR(50),
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    stdout LONGTEXT,
    stderr LONGTEXT,
    exit_code INT,
    duration_ms INT,
    memory_used_mb FLOAT,
    sandbox_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    INDEX idx_task_id (task_id),
    INDEX idx_status (status)
);

-- Memory 表 (Agent 记忆)
CREATE TABLE memory (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    content LONGTEXT NOT NULL,
    type ENUM('short_term', 'long_term') DEFAULT 'long_term',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_type (type)
);

-- Conversation 表 (对话历史)
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    INDEX idx_task_id (task_id),
    INDEX idx_created_at (created_at)
);
```

---

## 6. Elasticsearch 使用场景

### 6.1 索引设计

```json
// 向量记忆索引
{
  "index": "agent_memory_vectors",
  "mappings": {
    "properties": {
      "agent_id": { "type": "keyword" },
      "content": { "type": "text" },
      "embedding": { "type": "dense_vector", "dims": 1536 },
      "type": { "type": "keyword" },
      "created_at": { "type": "date" },
      "metadata": { "type": "object" }
    }
  }
}

// 执行日志索引
{
  "index": "execution_logs",
  "mappings": {
    "properties": {
      "task_id": { "type": "keyword" },
      "execution_id": { "type": "keyword" },
      "level": { "type": "keyword" },
      "message": { "type": "text" },
      "timestamp": { "type": "date" },
      "metadata": { "type": "object" }
    }
  }
}
```

---

## 7. API 设计

### 7.1 核心端点

```
# Agent 管理
POST   /api/agents                    # 创建 Agent
GET    /api/agents                    # 列表 Agent
GET    /api/agents/{agent_id}         # 获取 Agent 详情
PUT    /api/agents/{agent_id}         # 更新 Agent
DELETE /api/agents/{agent_id}         # 删除 Agent

# 任务执行
POST   /api/agents/{agent_id}/execute # 执行任务
GET    /api/tasks/{task_id}           # 获取任务状态
GET    /api/tasks/{task_id}/stream    # 流式获取任务结果
GET    /api/tasks                     # 列表任务

# 代码执行
POST   /api/sandbox/execute           # 执行代码
GET    /api/executions/{execution_id} # 获取执行结果

# 记忆管理
GET    /api/agents/{agent_id}/memory  # 获取 Agent 记忆
POST   /api/agents/{agent_id}/memory  # 添加记忆
```

---

## 8. 执行流程详解

### 8.1 DeepAgent 执行循环

```
┌─────────────────────────────────────────────────────────┐
│ 1. 用户请求                                             │
│    POST /api/agents/{agent_id}/execute                 │
│    Body: { task: "...", context: {...} }              │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│ 2. 请求验证 & 任务创建                                  │
│    - 验证 Agent 存在                                    │
│    - 创建 Task 记录 (MySQL)                            │
│    - 初始化 LangGraph State                            │
│    - 创建 Thread ID (用于记忆管理)                     │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│ 3. DeepAgent 执行循环 (LangGraph Runtime)              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ a) Planning (任务规划)                          │   │
│  │    - DeepAgent 内置 Planning Tool               │   │
│  │    - 分解任务为子任务                           │   │
│  │    - 生成执行计划                               │   │
│  │    - 保存到 Task.plan                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ b) LLM 推理 & 工具调用                          │   │
│  │    - 读取记忆 (Short-term + Long-term)          │   │
│  │    - 调用 LLM (OpenAI/Claude/Ollama)            │   │
│  │    - 解析响应 (思考/工具调用/完成)              │   │
│  │                                                 │   │
│  │    工具类型:                                    │   │
│  │    ├─ 内置工具 (Web 搜索、数据查询等)          │   │
│  │    ├─ MCP 工具 (外部服务)                      │   │
│  │    ├─ Skills (复杂工作流)                      │   │
│  │    └─ 代码执行 (OpenSandbox) ──┐               │   │
│  └─────────────────────────────────┼───────────────┘   │
│                                    │                   │
│  ┌─────────────────────────────────▼───────────────┐   │
│  │ c) 代码执行 (OpenSandbox)                       │   │
│  │    ├─ 创建 Sandbox 实例                         │   │
│  │    ├─ 执行代码/命令                             │   │
│  │    ├─ 收集结果 (stdout/stderr/exit_code)        │   │
│  │    ├─ 保存到 MySQL (executions 表)              │   │
│  │    └─ 返回给 Agent                              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ d) Subagent 委托 (可选)                         │   │
│  │    - DeepAgent 可以创建子 Agent                 │   │
│  │    - 委托子任务给子 Agent                       │   │
│  │    - 保持上下文隔离                             │   │
│  │    - 收集子 Agent 结果                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ e) Filesystem 操作 (可选)                       │   │
│  │    - DeepAgent 内置文件系统                     │   │
│  │    - 读写临时文件                               │   │
│  │    - 管理工作目录                               │   │
│  │    - 保存中间结果                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ f) 记忆更新                                     │   │
│  │    - 更新短期记忆 (LangGraph Checkpointer)      │   │
│  │    - 存储长期记忆 (Elasticsearch)               │   │
│  │    - Token 管理和优化                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Until: 任务完成或超时                                 │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│ 4. 结果处理                                             │
│    - 保存最终结果 (MySQL)                              │
│    - 更新 Task 状态                                    │
│    - 清理临时资源                                      │
│    - 返回给客户端                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 9. MCP (Model Context Protocol) 集成

### 9.1 MCP 架构

```
┌─────────────────────────────────────────────────────────┐
│                  DeepAgent                              │
│              (Tool Calling Loop)                        │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │ Tool Registry   │
        │ (内置 + MCP)    │
        └────────┬────────┘
                 │
        ┌────────▼────────────────────────┐
        │                                 │
┌───────▼──────────┐          ┌──────────▼──────────┐
│ 内置工具         │          │ MCP 工具            │
│ - Web Search     │          │ - 数据库查询        │
│ - Code Exec      │          │ - API 调用          │
│ - File Ops       │          │ - 自定义服务        │
└──────────────────┘          └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  MCP Server        │
                              │  (FastAPI/stdio)   │
                              │                    │
                              │ - Tool Definitions │
                              │ - Resource Access  │
                              │ - Prompts          │
                              └────────────────────┘
```

### 9.2 MCP 工具集成

```python
# MCP 客户端实现
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPToolManager:
    """MCP 工具管理器"""
    def __init__(self):
        self.clients: Dict[str, ClientSession] = {}
        self.tools: Dict[str, StructuredTool] = {}
    
    async def register_mcp_server(self, server_name: str, config: Dict):
        """注册 MCP 服务器"""
        # 支持 stdio 和 HTTP 传输
        if config.get("transport") == "stdio":
            params = StdioServerParameters(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {})
            )
            async with stdio_client(params) as client:
                self.clients[server_name] = client
                await self._load_tools_from_server(server_name, client)
        elif config.get("transport") == "http":
            # HTTP 传输支持
            pass
    
    async def _load_tools_from_server(self, server_name: str, client: ClientSession):
        """从 MCP 服务器加载工具"""
        tools = await client.list_tools()
        for tool in tools.tools:
            # 包装 MCP 工具为 LangChain StructuredTool
            structured_tool = self._wrap_mcp_tool(server_name, tool, client)
            self.tools[tool.name] = structured_tool
    
    def _wrap_mcp_tool(self, server_name: str, mcp_tool, client) -> StructuredTool:
        """将 MCP 工具包装为 LangChain StructuredTool"""
        async def tool_func(**kwargs):
            result = await client.call_tool(mcp_tool.name, kwargs)
            return result.content[0].text if result.content else ""
        
        # 从 MCP 工具定义生成 Pydantic 模型
        input_schema = self._generate_schema(mcp_tool.inputSchema)
        
        return StructuredTool.from_function(
            name=mcp_tool.name,
            description=mcp_tool.description,
            func=tool_func,
            args_schema=input_schema,
        )
    
    def _generate_schema(self, json_schema: Dict) -> type:
        """从 JSON Schema 生成 Pydantic 模型"""
        # 动态生成 Pydantic 模型
        pass

# MCP 配置示例
MCP_CONFIG = {
    "servers": {
        "database": {
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "mcp_database_server"],
            "env": {"DB_URL": "postgresql://..."}
        },
        "web_api": {
            "transport": "http",
            "url": "http://localhost:8001",
            "auth": {"type": "bearer", "token": "..."}
        }
    }
}
```

### 9.3 MCP 资源和提示

```python
# MCP 资源访问
class MCPResourceManager:
    """MCP 资源管理器"""
    async def read_resource(self, server_name: str, uri: str) -> str:
        """读取 MCP 资源"""
        client = self.clients[server_name]
        resource = await client.read_resource(uri)
        return resource.contents[0].text
    
    async def list_resources(self, server_name: str) -> List[str]:
        """列出 MCP 资源"""
        client = self.clients[server_name]
        resources = await client.list_resources()
        return [r.uri for r in resources.resources]

# MCP 提示 (Prompts)
class MCPPromptManager:
    """MCP 提示管理器"""
    async def get_prompt(self, server_name: str, name: str, args: Dict) -> str:
        """获取 MCP 提示"""
        client = self.clients[server_name]
        prompt = await client.get_prompt(name, args)
        return prompt.messages[0].content.text
```

---

## 10. 依赖包清单

```
# 核心框架
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# DeepAgents & LangChain
deepagents==0.1.0  # DeepAgents 核心
langchain==0.3.0
langchain-core==0.3.0
langchain-community==0.3.0
langgraph==0.2.0
langchain-openai==0.2.0
langchain-anthropic==0.2.0

# MCP 支持
mcp==1.0.0  # Model Context Protocol

# OpenSandbox
opensandbox-server==0.1.0
opensandbox-code-interpreter==0.1.0

# 数据库
sqlalchemy==2.0.23
pymysql==1.1.0
alembic==1.13.0
asyncpg==0.29.0  # PostgreSQL 异步驱动 (用于 LangGraph checkpointer)

# 缓存 & 消息队列
redis==5.0.1
celery==5.3.4
flower==2.0.1

# 向量库
elasticsearch==8.11.0

# 工具库
requests==2.31.0
python-dotenv==1.0.0
aiohttp==3.9.1
httpx==0.25.2

# 日志
python-json-logger==2.0.7

# 其他
pyyaml==6.0.1
```

---

## 11. 部署架构

### 11.1 Docker Compose 配置

```yaml
version: '3.8'

services:
  # MySQL
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: agent_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  # OpenSandbox Server
  opensandbox:
    image: opensandbox/server:latest
    ports:
      - "8001:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - SANDBOX_RUNTIME=docker

  # FastAPI Backend
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
      - elasticsearch
      - opensandbox
    environment:
      - DATABASE_URL=mysql+pymysql://root:root@mysql:3306/agent_db
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - OPENSANDBOX_URL=http://opensandbox:8000

  # Celery Worker
  celery:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - redis
      - mysql
    environment:
      - DATABASE_URL=mysql+pymysql://root:root@mysql:3306/agent_db
      - REDIS_URL=redis://redis:6379

volumes:
  mysql_data:
  es_data:
```

---

## 12. 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **Agent 框架** | DeepAgents | LangChain 官方 agent harness，内置规划、文件系统、子 Agent、记忆管理 |
| **底层运行时** | LangGraph | 支持有状态执行、流式处理、持久化检查点 |
| **Sandbox 方案** | OpenSandbox | 开源、功能完整、支持多语言、社区活跃 |
| **隔离方式** | Docker 容器 | 安全性高、资源限制灵活、易于扩展 |
| **执行队列** | Redis + Celery | 分布式、可扩展、支持优先级 |
| **向量库** | Elasticsearch | 支持向量搜索、日志聚合、全文搜索 |
| **数据库** | MySQL | 结构化数据、事务支持、易于扩展 |
| **LLM 集成** | 多提供商支持 | 灵活切换、成本优化 |
| **协议支持** | MCP | 标准化工具集成、生态扩展 |
| **实时通信** | WebSocket | 流式返回结果、实时反馈 |

---

## 13. 下一步实现计划

### 第一阶段：基础框架 (1-2 周)
- [ ] FastAPI 项目初始化
- [ ] MySQL 数据库设计和迁移
- [ ] Redis 集成
- [ ] 基础 API 端点
- [ ] LangGraph Checkpointer 配置

### 第二阶段：核心 Agent 系统 (2-3 周)
- [ ] DeepAgent 工厂实现
- [ ] LLM 集成 (OpenAI/Claude/Ollama)
- [ ] 工具系统框架
- [ ] OpenSandbox 集成
- [ ] 内置工具实现 (Web 搜索、代码执行等)

### 第三阶段：高级功能 (2-3 周)
- [ ] 记忆系统 (短期 + 长期)
- [ ] Elasticsearch 集成
- [ ] MCP 服务器集成
- [ ] 多 Agent 协作
- [ ] 流式响应

### 第四阶段：Skills 系统 (2 周)
- [ ] Skills 管理器实现
- [ ] Skills 加载和执行
- [ ] Skills 市场 API
- [ ] Skills 版本管理

### 第五阶段：前端和部署 (1-2 周)
- [ ] Next.js 前端开发
- [ ] Docker 容器化
- [ ] 部署和测试
- [ ] 监控和日志

---

## 14. 快速开始指南

### 14.1 本地开发环境

```bash
# 1. 克隆项目
git clone <repo>
cd agent-system

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r backend/requirements.txt

# 4. 启动 Docker 服务
docker-compose up -d

# 5. 初始化数据库
cd backend
alembic upgrade head

# 6. 启动后端服务
uvicorn app.main:app --reload

# 7. 启动前端 (另一个终端)
cd frontend
npm install
npm run dev
```

### 14.2 创建第一个 Agent

```python
from app.agents.factory import DeepAgentFactory
from app.llm.factory import LLMFactory
from app.llm.config import LLMConfig

# 创建 LLM
llm = LLMFactory.create(LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="sk-...",
))

# 创建 Agent
factory = DeepAgentFactory()
agent = factory.create_agent(
    name="research_agent",
    model=llm,
    tools=["web_search", "code_execution"],
    system_prompt="You are a research assistant...",
)

# 执行任务
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Research AI agents"}]
})
```

### 14.3 注册 MCP 服务器

```python
from app.tools.mcp.client import MCPToolManager

mcp_manager = MCPToolManager()

# 注册 stdio 服务器
await mcp_manager.register_mcp_server("database", {
    "transport": "stdio",
    "command": "python",
    "args": ["-m", "mcp_database_server"],
})

# 现在可以在 Agent 中使用 MCP 工具
```

---

## 15. 常见问题 (FAQ)

### Q: DeepAgents 与其他 Agent 框架的区别？
A: DeepAgents 是 LangChain 官方的 agent harness，提供了内置的规划、文件系统、子 Agent 和记忆管理能力，特别适合复杂、长期的任务。相比 LangChain 的基础 Agent，DeepAgents 提供了更高层的抽象和更多的开箱即用功能。

### Q: 如何处理长时间运行的任务？
A: 使用 LangGraph 的 Checkpointer 进行持久化，支持任务暂停、恢复和断点续传。同时使用 Celery 进行异步任务队列管理。

### Q: 如何扩展系统支持新的工具？
A: 有三种方式：
1. 实现 LangChain StructuredTool 并注册到 ToolRegistry
2. 通过 MCP 协议集成外部服务
3. 创建 Skill 进行复杂工作流编排

### Q: 代码执行的安全性如何保证？
A: 使用 OpenSandbox 提供的 Docker 隔离、资源限制、网络隔离等多层防护。同时支持自定义沙箱配置。

### Q: 如何监控 Agent 执行状态？
A: 通过 LangSmith 进行原生追踪，同时将执行日志存储到 Elasticsearch，支持实时监控和历史查询。

---

## 16. 需要进一步讨论的问题

1. **多 Agent 协作**
   - 如何处理 Agent 之间的通信和协调？
   - 是否需要 Agent 编排语言或工作流引擎？
   - 如何管理 Agent 之间的上下文共享？

2. **错误恢复和容错**
   - 任务失败后的重试策略？
   - 是否支持自动降级和备选方案？
   - 如何处理部分失败的情况？

3. **安全性和权限**
   - 代码执行的沙箱逃逸防护？
   - 用户权限隔离和多租户支持？
   - Skill 权限管理和审计？
   - API 密钥和敏感信息管理？

4. **性能优化**
   - Token 缓存和重用策略？
   - 并发执行的限制和优化？
   - Skill 执行的性能基准？
   - 向量搜索的性能优化？

5. **监控和可观测性**
   - 如何监控 Agent 执行状态和性能？
   - 日志聚合和分析方案？
   - Skill 执行的监控和告警？
   - 成本追踪和优化？

6. **生态和集成**
   - 如何与现有系统集成？
   - 是否支持自定义 LLM 提供商？
   - 如何扩展 Skills 生态？
   - 是否支持 Agent 市场和分享？

---

## 17. 参考资源

### 官方文档
- [DeepAgents 文档](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [OpenSandbox GitHub](https://github.com/alibaba/OpenSandbox)
- [MCP 规范](https://modelcontextprotocol.io/)

### 相关项目
- [Manus Agent Skills](https://manus.im/features/agent-skills)
- [Claude Agent SDK](https://github.com/anthropics/anthropic-sdk-python)
- [CrewAI](https://github.com/joaomdmoura/crewai)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)

### 学习资源
- [Agent Skills Open Standard](https://inference.sh/blog/skills/agent-skills-overview)
- [Deep Agents Part 1: Beyond 'Shallow'](https://colinmcnamara.com/blog/deep-agents-part-1-beyond-shallow)
- [Streaming deepagents and task delegation](https://dogukantuna.me/blog/streaming-deep-agents-and-task-delegation)
- [LangSmith 追踪指南](https://docs.langchain.com/langsmith/trace-deep-agents)

---

## 18. 更新日志

### v0.1.0 (2025-03-04)
- 初始架构设计
- 基于 DeepAgents 框架
- 集成 MCP 协议支持
- 完整的 Skills 系统设计
- OpenSandbox 集成方案

---

**最后更新**: 2025-03-04
**维护者**: AI Agent System Team
**许可证**: MIT