"""Sandbox Configuration

Configuration models for code execution sandbox.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    """Configuration for code execution sandbox"""

    timeout: int = Field(default=30, description="Execution timeout in seconds")
    memory_limit: int = Field(default=512, description="Memory limit in MB")
    cpu_limit: float = Field(default=1.0, description="CPU limit")
    network_enabled: bool = Field(default=False, description="Enable network access")
    environment: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )


class ExecutionResult(BaseModel):
    """Result of code execution"""

    stdout: str = Field(description="Standard output")
    stderr: str = Field(description="Standard error")
    exit_code: int = Field(description="Exit code")
    duration_ms: int = Field(description="Execution duration in milliseconds")
    memory_used_mb: Optional[float] = Field(
        default=None, description="Memory used in MB"
    )
    error: Optional[str] = Field(default=None, description="Error message")
