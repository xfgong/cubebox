"""Unit tests for tool system

Tests the calculator tool and tool registry functionality.
"""

from cubebox.tools import get_registry
from cubebox.tools.builtin.calculator import calculator, create_calculator_tool


class TestCalculatorTool:
    """Tests for calculator tool"""

    def test_calculator_tool_creation(self) -> None:
        """Test calculator tool is created

        Validates: Requirements 3.1, 3.4
        """
        tool = create_calculator_tool()

        assert tool is not None
        assert tool.name == "calculator"
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_calculator_basic_math(self) -> None:
        """Test calculator with simple arithmetic (2 + 3)

        Validates: Requirements 3.2
        """
        result = calculator("2 + 3")

        assert result is not None
        assert "5" in result
        assert "Result:" in result

    def test_calculator_complex_math(self) -> None:
        """Test calculator with complex expression

        Validates: Requirements 3.2
        """
        result = calculator("2 + 3 * 4")

        assert result is not None
        assert "14" in result
        assert "Result:" in result

    def test_calculator_multiplication(self) -> None:
        """Test calculator with multiplication

        Validates: Requirements 3.2
        """
        result = calculator("5 * 6")

        assert result is not None
        assert "30" in result

    def test_calculator_division(self) -> None:
        """Test calculator with division

        Validates: Requirements 3.2
        """
        result = calculator("10 / 2")

        assert result is not None
        assert "5" in result

    def test_calculator_error_handling(self) -> None:
        """Test calculator with invalid expression

        Validates: Requirements 3.3
        """
        result = calculator("invalid expression !!!")

        assert result is not None
        assert "Error:" in result

    def test_calculator_division_by_zero(self) -> None:
        """Test calculator with division by zero

        Validates: Requirements 3.3
        """
        result = calculator("10 / 0")

        assert result is not None
        assert "Error:" in result
        assert "Division by zero" in result

    def test_calculator_syntax_error(self) -> None:
        """Test calculator with syntax error

        Validates: Requirements 3.3
        """
        result = calculator("2 + * 3")

        assert result is not None
        assert "Error:" in result

    def test_calculator_with_math_functions(self) -> None:
        """Test calculator with math functions

        Validates: Requirements 3.2
        """
        result = calculator("sqrt(16)")

        assert result is not None
        assert "4" in result


class TestToolRegistry:
    """Tests for tool registry"""

    def test_tool_registry_loaded(self) -> None:
        """Test calculator tool is in registry

        Validates: Requirements 3.1, 3.4
        """
        registry = get_registry()

        assert registry is not None
        tools = registry.list_tools()
        assert len(tools) > 0

    def test_tool_registry_has_calculator(self) -> None:
        """Test registry contains calculator tool

        Validates: Requirements 3.1, 3.4
        """
        registry = get_registry()
        tools = registry.list_tools()

        tool_names = [tool.name for tool in tools]
        assert "calculator" in tool_names

    def test_tool_registry_get_tool(self) -> None:
        """Test getting tool by name

        Validates: Requirements 3.1
        """
        registry = get_registry()

        tool = registry.get_tool("calculator")
        assert tool is not None
        assert tool.name == "calculator"

    def test_tool_registry_get_nonexistent_tool(self) -> None:
        """Test getting nonexistent tool returns None

        Validates: Requirements 3.1
        """
        registry = get_registry()

        tool = registry.get_tool("nonexistent_tool")
        assert tool is None
