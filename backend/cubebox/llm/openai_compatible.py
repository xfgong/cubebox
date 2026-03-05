"""OpenAI-Compatible Chat Model with Reasoning Support

Extends ChatOpenAI to extract reasoning_content field from Chat Completions API.
This is useful for OpenAI-compatible endpoints that return reasoning in the response.
"""

from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_openai import ChatOpenAI


class ChatOpenAICompatible(ChatOpenAI):
    """OpenAI-compatible chat model with reasoning_content extraction.

    This class extends ChatOpenAI to extract reasoning_content from the API
    response. Many OpenAI-compatible endpoints (like DeepSeek, DouBao, Qwen)
    return reasoning in the message.reasoning_content field.

    The reasoning_content will be available in:
    - response.additional_kwargs["reasoning_content"]

    Example:
        ```python
        from cubebox.llm import ChatOpenAICompatible

        llm = ChatOpenAICompatible(
            model="doubao-seed-1.6-lite-thinking",
            base_url="https://gateway.chat.sensedeal.vip/v1",
            api_key="your-key",
        )

        response = llm.invoke("What is 3^3?")

        # Access reasoning content
        reasoning = response.additional_kwargs.get("reasoning_content")
        if reasoning:
            print(f"Reasoning: {reasoning}")
        print(f"Answer: {response.content}")
        ```
    """

    def _create_chat_result(
        self,
        response: Any,
        generation_info: dict[str, Any] | None = None,
    ) -> ChatResult:
        """Create ChatResult from API response, extracting reasoning_content.

        This method extends the parent implementation to extract reasoning_content
        from the response while maintaining all other functionality.

        Args:
            response: Raw API response from OpenAI SDK
            generation_info: Additional generation info

        Returns:
            ChatResult with reasoning_content in additional_kwargs
        """
        # Call parent method to get base result
        result = super()._create_chat_result(response, generation_info)

        # Extract reasoning_content if available (only for non-dict responses)
        if not isinstance(response, dict) and hasattr(response, "choices"):
            for i, res in enumerate(response.choices):
                if hasattr(res.message, "reasoning_content") and res.message.reasoning_content:
                    if i < len(result.generations):
                        message = result.generations[i].message
                        if isinstance(message, AIMessage):
                            message.additional_kwargs["reasoning_content"] = (
                                res.message.reasoning_content
                            )

        return result

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict[str, Any],
        default_chunk_class: type,
        base_generation_info: dict[str, Any] | None,
    ) -> ChatGenerationChunk | None:
        """Convert chunk to generation chunk, extracting reasoning_content.

        This method extends the parent implementation to extract reasoning_content
        from streaming chunks while maintaining all other functionality.

        Args:
            chunk: Chunk dictionary from streaming response
            default_chunk_class: Default message chunk class
            base_generation_info: Base generation info

        Returns:
            ChatGenerationChunk with reasoning_content if available
        """
        # Call parent method to get base chunk
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )

        if generation_chunk is None:
            return None

        # Extract reasoning_content from delta if available
        choices = chunk.get("choices", []) or chunk.get("chunk", {}).get("choices", [])
        if choices:
            choice = choices[0]
            delta = choice.get("delta")
            if delta and "reasoning_content" in delta:
                reasoning_content = delta["reasoning_content"]
                if reasoning_content and isinstance(generation_chunk.message, AIMessageChunk):
                    generation_chunk.message.additional_kwargs["reasoning_content"] = (
                        reasoning_content
                    )

        return generation_chunk

    @property
    def _llm_type(self) -> str:
        """Return identifier for this model type."""
        return "openai-compatible"
