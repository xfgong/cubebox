# Implementation Plan: DeepAgentExecutor MVP (Simplified)

## Overview

This implementation plan breaks down the simplified DeepAgentExecutor MVP design into discrete, incremental coding tasks. The implementation follows a bottom-up approach: core models → executor → tools → API → testing.

**Key Simplifications**:
- Single input parameter (user question)
- Direct DeepAgent creation (no AgentConfig)
- Streaming output with Server-Sent Events (SSE)

## Tasks

- [x] 1. Set up project structure and core data models
  - Create schemas.py in backend/cubebox/agents/
  - Define ExecuteRequest model (only "input" field)
  - Define AgentEvent model and event type variants (ChainStartEvent, LLMStartEvent, etc.)
  - Add proper validation and type hints
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement calculator tool
  - Create calculator.py in backend/cubebox/tools/builtin/
  - Define CalculatorInput Pydantic model with expression field
  - Implement calculator function with safe evaluation
  - Create StructuredTool from calculator function
  - Add error handling for invalid expressions
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Implement tool registry initialization
  - Update backend/cubebox/tools/__init__.py to export ToolRegistry
  - Create tool registry instance and register calculator tool
  - Ensure tools are available for agent loading
  - _Requirements: 3.1, 3.4_

- [x] 4. Implement DeepAgentExecutor core class
  - Create executor.py in backend/cubebox/agents/
  - Implement __init__ method (no config needed)
  - Implement _create_agent() method to instantiate DeepAgent
  - Implement _load_tools() method to fetch tools from registry
  - Implement stream() async method for streaming execution
  - Add event conversion logic (LangChain events → AgentEvent)
  - Add error handling and logging throughout
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5. Implement API error handling
  - Create exceptions.py in backend/cubebox/api/
  - Define custom exception classes (InvalidInputError, ExecutionError, etc.)
  - Implement error event formatting
  - Add exception handlers to FastAPI app
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6. Implement POST /api/v1/agents/run endpoint
  - Create agents.py in backend/cubebox/api/routes/v1/
  - Implement run_agent() endpoint handler with streaming response
  - Add request validation (ExecuteRequest)
  - Integrate DeepAgentExecutor for streaming execution
  - Return SSE formatted event stream
  - Handle errors and send error events
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Implement logging system
  - Create logger.py in backend/cubebox/utils/
  - Configure Python logging with proper format and levels
  - Add structured logging for key events (request start, LLM calls, tool calls, completion)
  - Ensure error logs include stack traces
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 8. Checkpoint - Ensure core functionality works
  - Run all unit tests for executor, tools, and API
  - Verify no import errors or type issues
  - Test basic agent creation and streaming execution
  - Ensure all tests pass

- [x] 9. Implement E2E test framework
  - Create conftest.py in tests/ with pytest fixtures
  - Implement test utilities for creating test executor
  - Implement test utilities for executing tasks via API
  - Create test client for API testing with SSE support
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 10. Implement E2E test cases
  - Create test_executor.py with unit tests for DeepAgentExecutor
  - Create test_tools.py with unit tests for tool system
  - Create test_api.py with E2E tests for streaming API endpoint
  - Test simple calculation task with streaming events
  - Test error handling and validation
  - Test event stream completeness (chain_start → chain_end)
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Run complete test suite (unit + E2E tests)
  - Verify code quality with make check
  - Format code with make format
  - Run type checking with make type-check
  - Ensure all tests pass

## Notes

- Each task references specific requirements for traceability
- Implementation uses Python 3.12+ with full type hints
- Code must pass `make check` before completion
- All code follows project style guide (100 char line length, black formatting, ruff linting)
- Streaming output uses Server-Sent Events (SSE) format
- Event stream should include: chain_start, llm_start, llm_end, tool_start, tool_end, chain_end, error, done
