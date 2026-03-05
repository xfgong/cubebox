"""Calculator Tool

A simple calculator tool for performing mathematical expressions.
Provides safe evaluation of mathematical expressions.
"""

import math
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """Input schema for calculator tool"""

    expression: str = Field(description="Mathematical expression to evaluate, e.g., '2 + 3 * 4'")


def calculator(expression: str) -> str:
    """
    Execute a simple mathematical calculation.

    Safely evaluates mathematical expressions using a restricted
    namespace to prevent code injection.

    Args:
        expression: Mathematical expression string

    Returns:
        Result string with the calculation result or error message
    """
    try:
        # Create a safe namespace with only math functions
        safe_dict: dict[str, Any] = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "__builtins__": {},
        }
        # Add common math functions
        safe_dict.update(
            {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
        )

        # Evaluate the expression
        result = eval(expression, safe_dict)
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Error: Invalid value - {str(e)}"
    except SyntaxError:
        return "Error: Invalid expression syntax"
    except NameError as e:
        return f"Error: Undefined variable - {str(e)}"
    except TypeError as e:
        return f"Error: Invalid operation - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def create_calculator_tool() -> StructuredTool:
    """
    Create a StructuredTool for the calculator.

    Returns:
        StructuredTool instance for calculator
    """
    return StructuredTool.from_function(
        func=calculator,
        name="calculator",
        description="Execute simple mathematical calculations. "
        "Supports basic arithmetic, trigonometric, and math functions.",
        args_schema=CalculatorInput,
    )
