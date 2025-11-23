"""
Calculator/Math Tool for ARK Agent AGI
Provides advanced mathematical operations
"""

import math
from typing import Any, Dict

from tools.base import BaseTool
from utils.observability.logging_utils import log_event


class CalculatorTool(BaseTool):
    """
    Advanced mathematical operations and expression evaluation
    """

    def __init__(self):
        super().__init__(name="calculator", description="Evaluate mathematical expressions")
        # Safe math functions
        self.safe_functions = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sqrt": math.sqrt,
            "pow": pow,
            "exp": math.exp,
            "log": math.log,
            "log10": math.log10,
            "log2": math.log2,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "ceil": math.ceil,
            "floor": math.floor,
            "trunc": math.trunc,
            "pi": math.pi,
            "e": math.e,
        }
        log_event("CalculatorTool", {"event": "initialized"})

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute calculator operations.
        Args:
            expression (str): Math expression to evaluate
            numbers (list): List of numbers for statistics (optional)
            operation (str): 'calculate' or 'statistics' (default: 'calculate')
        """
        operation = kwargs.get("operation", "calculate")
        
        if operation == "statistics":
            return self.statistics(kwargs.get("numbers", []))
        
        return self.calculate(kwargs.get("expression", ""))

    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression safely

        Args:
            expression: Math expression to evaluate

        Returns:
            Calculation result
        """
        try:
            # Clean the expression
            expression = expression.strip()

            # Create safe evaluation namespace
            safe_dict: Dict[str, Any] = {"__builtins__": {}}
            safe_dict.update(self.safe_functions)

            # Evaluate the expression
            result = eval(expression, safe_dict)

            log_event(
                "CalculatorTool",
                {"event": "calculation_success", "expression": expression, "result": result},
            )

            return {
                "success": True,
                "expression": expression,
                "result": result,
                "formatted": f"{expression} = {result}",
            }

        except Exception as e:
            log_event(
                "CalculatorTool",
                {"event": "calculation_error", "expression": expression, "error": str(e)},
            )

            return {
                "success": False,
                "expression": expression,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def statistics(self, numbers: list) -> Dict[str, Any]:
        """Calculate statistics for a list of numbers"""
        try:
            return {
                "success": True,
                "count": len(numbers),
                "sum": sum(numbers),
                "mean": sum(numbers) / len(numbers),
                "min": min(numbers),
                "max": max(numbers),
                "range": max(numbers) - min(numbers),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


calculator = CalculatorTool()
