"""Tool Registry

Manages registration and retrieval of tools for agents.
Supports both built-in tools and MCP-provided tools.
"""

from typing import Any

from langchain_core.tools import StructuredTool


class ToolRegistry:
    """Registry for managing agent tools"""

    def __init__(self) -> None:
        """Initialize the tool registry"""
        self._tools: dict[str, StructuredTool] = {}
        self._mcp_clients: dict[str, Any] = {}

    def register_tool(self, tool: StructuredTool) -> None:
        """
        Register a built-in tool.

        Args:
            tool: StructuredTool instance to register
        """
        self._tools[tool.name] = tool

    def register_mcp_server(self, server_name: str, config: dict[str, Any]) -> None:
        """
        Register an MCP server.

        Args:
            server_name: Name of the MCP server
            config: MCP server configuration
        """
        # TODO: Implement MCP server registration
        pass

    def get_tool(self, name: str) -> StructuredTool | None:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            StructuredTool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> list[StructuredTool]:
        """
        List all registered tools.

        Returns:
            List of StructuredTool instances
        """
        return list(self._tools.values())

    def list_tool_names(self) -> list[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())
