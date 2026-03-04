"""LLM Factory

Creates LLM instances based on configuration.
Supports multiple providers: OpenAI, Anthropic, Ollama, etc.
"""

from typing import Any

from langchain_openai import ChatOpenAI

from cubebox.llm.config import LLMConfig


class LLMFactory:
    """Factory for creating LLM instances"""

    @staticmethod
    def create(config: LLMConfig) -> Any:
        """
        Create an LLM instance based on configuration.

        Args:
            config: LLM configuration

        Returns:
            LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        if config.provider == "openai":
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        elif config.provider == "anthropic":
            # TODO: Implement Anthropic support
            raise NotImplementedError("Anthropic provider not yet implemented")
        elif config.provider == "ollama":
            # TODO: Implement Ollama support
            raise NotImplementedError("Ollama provider not yet implemented")
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
