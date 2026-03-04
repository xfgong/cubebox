"""Agent Configuration Models

Defines Pydantic models for agent configuration and management.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for an Agent"""

    id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Agent name")
    role: str = Field(description="Agent role/purpose")
    description: Optional[str] = Field(default=None, description="Agent description")
    system_prompt: str = Field(description="System prompt for the agent")
    model: str = Field(description="LLM model identifier")
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    skills: List[str] = Field(default_factory=list, description="List of skill names")
    planning_enabled: bool = Field(default=True, description="Enable task planning")
    filesystem_enabled: bool = Field(
        default=True, description="Enable filesystem access"
    )
    subagents_enabled: bool = Field(
        default=True, description="Enable subagent spawning"
    )
    memory_config: Dict[str, Any] = Field(
        default_factory=dict, description="Memory configuration"
    )
    mcp_servers: List[str] = Field(default_factory=list, description="MCP server names")


class TaskStatus(str):
    """Task status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """Task model for agent execution"""

    id: str = Field(description="Unique task identifier")
    agent_id: str = Field(description="Agent ID")
    description: str = Field(description="Task description")
    expected_output: Optional[str] = Field(
        default=None, description="Expected output description"
    )
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data")
    status: str = Field(default=TaskStatus.PENDING, description="Task status")
    output_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Output data"
    )
    plan: Optional[List[str]] = Field(default=None, description="Execution plan")
    subtasks: List[str] = Field(default_factory=list, description="Subtask IDs")
    parent_task_id: Optional[str] = Field(default=None, description="Parent task ID")
