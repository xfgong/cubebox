"""LLM Configuration Models

Defines configuration for different LLM providers.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""

    provider: str = Field(description="LLM provider (openai, anthropic, ollama, etc.)")
    model: str = Field(description="Model identifier")
    api_key: Optional[str] = Field(default=None, description="API key")
    base_url: Optional[str] = Field(default=None, description="Base URL for API")
    temperature: float = Field(default=0.7, description="Temperature parameter")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
