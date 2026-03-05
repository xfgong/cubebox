"""Tool system module"""

from cubebox.tools.builtin.calculator import create_calculator_tool
from cubebox.tools.registry import ToolRegistry

# Create global tool registry instance
_registry = ToolRegistry()

# Register built-in tools
_registry.register_tool(create_calculator_tool())


def get_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        ToolRegistry instance with all registered tools
    """
    return _registry


__all__ = ["ToolRegistry", "get_registry"]
