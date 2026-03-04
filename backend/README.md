# cubebox - Agent System Backend

AI Agent System Backend built on DeepAgents framework with LangChain and LangGraph.

## Project Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── app.py                    # Application state management
│   ├── config.py                 # Configuration management (dynaconf)
│   ├── agents/
│   │   ├── __init__.py
│   │   └── config.py             # Agent configuration models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                # FastAPI application factory
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py         # Health check endpoints
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── config.py             # LLM configuration models
│   │   └── factory.py            # LLM factory for multiple providers
│   ├── memory/
│   │   ├── __init__.py
│   │   └── manager.py            # Memory management (short/long-term)
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── client.py             # MCP protocol client
│   ├── sandbox/
│   │   ├── __init__.py
│   │   ├── config.py             # Sandbox configuration
│   │   └── executor.py           # Code execution in sandbox
│   ├── tools/
│   │   ├── __init__.py
│   │   └── registry.py           # Tool registry and management
│   └── utils/
│       ├── __init__.py
│       └── log.py                # Logging configuration
├── config.yaml                   # Base configuration
├── config.development.yaml       # Development overrides
├── config.production.yaml        # Production overrides
├── main.py                       # Application entry point
├── pyproject.toml               # Project metadata and dependencies
└── README.md                    # This file
```

## Setup

### Prerequisites

- Python 3.12+
- uv (Python package manager)

### Installation

1. Install dependencies:

```bash
cd backend
uv sync
```

2. Create a `.env` file for local configuration:

```bash
cp .env.example .env
```

3. Set required environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export ENV_FOR_DYNACONF="development"
```

## Running the Application

### Development

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Production

```bash
ENV_FOR_DYNACONF=production python main.py
```

## Configuration

Configuration is managed using dynaconf with YAML files:

- `config.yaml` - Base configuration
- `config.development.yaml` - Development overrides
- `config.production.yaml` - Production overrides
- Environment variables with `CUBEBOX_` prefix

Example:

```bash
export CUBEBOX_DEBUG=true
export CUBEBOX_LLM__PROVIDER=anthropic
```

## API Endpoints

### Health Check

```bash
GET /health
```

## Development

### Code Style

Format code with black and isort:

```bash
uv run black src/
uv run isort src/
```

### Testing

Run tests with pytest:

```bash
uv run pytest
```

## Architecture Overview

### Core Components

1. **Agent System** - DeepAgents-based agent framework
2. **LLM Integration** - Multi-provider LLM support (OpenAI, Anthropic, Ollama)
3. **Tool Registry** - Built-in and MCP tools management
4. **Memory System** - Short-term and long-term memory
5. **Sandbox Executor** - Isolated code execution (OpenSandbox)
6. **MCP Client** - Model Context Protocol integration

### Key Features

- Multi-agent coordination
- Task planning and execution
- Code execution in isolated sandboxes
- Long-term memory with vector search
- MCP protocol support for tool integration
- Comprehensive logging with loguru

## Next Steps

1. Implement database models and migrations
2. Add agent execution engine
3. Implement MCP server integration
4. Add sandbox execution with OpenSandbox
5. Implement memory persistence
6. Add comprehensive API endpoints
7. Add authentication and authorization
8. Add monitoring and tracing

## Dependencies

Key dependencies:

- **FastAPI** - Web framework
- **LangChain** - LLM framework
- **LangGraph** - Graph-based agent orchestration
- **Pydantic** - Data validation
- **Dynaconf** - Configuration management
- **Loguru** - Logging

See `pyproject.toml` for complete dependency list.

## License

MIT
