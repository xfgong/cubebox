"""DeepAgentExecutor

Core executor for running DeepAgent-based tasks with streaming support.
Handles agent creation, tool loading, and event streaming.
"""

import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import StructuredTool

from cubebox.agents.schemas import (
    AgentEvent,
    ChainEndEvent,
    ChainStartEvent,
    DoneEvent,
    ErrorEvent,
    LLMEndEvent,
    LLMStartEvent,
    ToolEndEvent,
    ToolStartEvent,
)
from cubebox.llm.factory import LLMFactory
from cubebox.tools import get_registry

logger = logging.getLogger(__name__)


class DeepAgentExecutor:
    """Executor for DeepAgent-based task execution with streaming support"""

    def __init__(self) -> None:
        """
        Initialize the DeepAgentExecutor.

        Creates LLM instance and loads tools from registry.
        """
        logger.info("Initializing DeepAgentExecutor")
        self.llm = self._create_llm()
        self.tools = self._load_tools()
        logger.info(f"DeepAgentExecutor initialized with {len(self.tools)} tools")

    def _create_llm(self) -> Any:
        """
        Create LLM instance using LLMFactory.

        Uses the default model from configuration.

        Returns:
            LLM instance (ChatOpenAI or ChatOpenAICompatible)

        Raises:
            ValueError: If model creation fails
        """
        try:
            factory = LLMFactory()
            # Use the first available model from the first provider
            providers = factory.list_providers()
            if not providers:
                raise ValueError("No LLM providers configured")

            provider_name = providers[0]
            models = factory.list_models(provider_name)
            if not models:
                raise ValueError(f"No models available in provider '{provider_name}'")

            model_id = models[0]
            logger.info(f"Creating LLM with model: {model_id} from provider: {provider_name}")
            llm = factory.create(model_id=model_id, provider_name=provider_name)
            return llm
        except Exception as e:
            logger.error(f"Failed to create LLM: {str(e)}")
            raise

    def _load_tools(self) -> list[StructuredTool]:
        """
        Load tools from the tool registry.

        Returns:
            List of StructuredTool instances
        """
        try:
            registry = get_registry()
            tools = registry.list_tools()
            logger.info(f"Loaded {len(tools)} tools from registry")
            for tool in tools:
                logger.debug(f"Tool available: {tool.name}")
            return tools
        except Exception as e:
            logger.error(f"Failed to load tools: {str(e)}")
            raise

    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO 8601 format.

        Returns:
            ISO 8601 formatted timestamp string
        """
        return datetime.now(UTC).isoformat()

    def _convert_event(self, event: dict[str, Any]) -> AgentEvent | None:
        """
        Convert LangChain event to AgentEvent.

        Args:
            event: LangChain event dictionary

        Returns:
            AgentEvent instance or None if event type not supported
        """
        event_type = event.get("event")
        timestamp = self._get_current_timestamp()

        try:
            if event_type == "on_chain_start":
                data = event.get("data", {})
                input_data = data.get("input", {})
                if isinstance(input_data, dict):
                    input_text = input_data.get("input", "")
                else:
                    input_text = str(input_data)
                return ChainStartEvent(
                    timestamp=timestamp,
                    data={"input": input_text},
                )

            elif event_type == "on_llm_start":
                data = event.get("data", {})
                return LLMStartEvent(
                    timestamp=timestamp,
                    data={
                        "model": data.get("model", "unknown"),
                        "messages": data.get("messages", []),
                    },
                )

            elif event_type == "on_llm_end":
                data = event.get("data", {})
                output = data.get("output", {})
                # Extract content from LangChain output
                content = ""
                if isinstance(output, dict):
                    if "content" in output:
                        content = output["content"]
                    elif "message" in output:
                        msg = output["message"]
                        if isinstance(msg, dict) and "content" in msg:
                            content = msg["content"]
                else:
                    content = str(output)

                usage = data.get("usage", {})
                return LLMEndEvent(
                    timestamp=timestamp,
                    data={
                        "output": content,
                        "usage": {
                            "input_tokens": usage.get("input_tokens", 0),
                            "output_tokens": usage.get("output_tokens", 0),
                        },
                    },
                )

            elif event_type == "on_tool_start":
                data = event.get("data", {})
                return ToolStartEvent(
                    timestamp=timestamp,
                    data={
                        "tool_name": data.get("tool_name", "unknown"),
                        "input": data.get("input", {}),
                    },
                )

            elif event_type == "on_tool_end":
                data = event.get("data", {})
                return ToolEndEvent(
                    timestamp=timestamp,
                    data={
                        "tool_name": data.get("tool_name", "unknown"),
                        "output": data.get("output", ""),
                    },
                )

            elif event_type == "on_chain_end":
                data = event.get("data", {})
                output = data.get("output", {})
                # Extract output content
                output_text = ""
                if isinstance(output, dict):
                    if "output" in output:
                        output_text = str(output["output"])
                    else:
                        output_text = str(output)
                else:
                    output_text = str(output)

                return ChainEndEvent(
                    timestamp=timestamp,
                    data={"output": output_text},
                )

            else:
                logger.debug(f"Unsupported event type: {event_type}")
                return None

        except Exception as e:
            logger.error(f"Error converting event {event_type}: {str(e)}")
            return None

    async def stream(self, input_text: str) -> AsyncIterator[AgentEvent]:
        """
        Stream agent execution with event conversion.

        Executes the agent with the given input and yields AgentEvent instances
        for each step in the execution.

        Args:
            input_text: User input question or task

        Yields:
            AgentEvent instances representing execution steps

        Raises:
            Exception: If agent execution fails
        """
        logger.info(f"Starting agent execution with input: {input_text[:100]}")

        try:
            # Import here to avoid circular imports
            from deepagents import create_deep_agent

            # Create agent
            agent = create_deep_agent(model=self.llm, tools=self.tools)
            logger.debug("Agent created successfully")

            # Yield chain start event
            yield ChainStartEvent(
                timestamp=self._get_current_timestamp(),
                data={"input": input_text},
            )

            # Stream events from agent
            event_count = 0
            async for chunk in agent.astream(
                {"messages": [{"role": "user", "content": input_text}]},
                stream_mode="updates",
            ):
                event_count += 1
                logger.debug(f"Received chunk: {chunk}")

                # Convert and yield event
                # Note: chunk is a dict with node_name -> data mapping
                if isinstance(chunk, dict):
                    for node_name, data in chunk.items():
                        converted_event = self._convert_event(
                            {"event": f"on_{node_name}", "data": data}
                        )
                        if converted_event:
                            yield converted_event

            logger.info(f"Agent execution completed with {event_count} chunks")

            # Yield done event
            yield DoneEvent(timestamp=self._get_current_timestamp())

        except Exception as e:
            logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
            # Yield error event
            yield ErrorEvent(
                timestamp=self._get_current_timestamp(),
                data={
                    "error_code": "EXECUTION_ERROR",
                    "message": "Agent execution failed",
                    "details": str(e),
                },
            )
            # Yield done event even on error
            yield DoneEvent(timestamp=self._get_current_timestamp())
