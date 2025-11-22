"""
Calculator/Math Tool for ARK Agent AGI
Provides advanced mathematical operations
"""

import math
import re
from typing import Dict, Any, Union
from src.utils.logging_utils import log_event

class CalculatorTool:
    """
    Advanced mathematical operations and expression evaluation
    """
    
    def __init__(self):
        # Safe math functions
        self.safe_functions = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sqrt': math.sqrt, 'pow': pow, 'exp': math.exp,
            'log': math.log, 'log10': math.log10, 'log2': math.log2,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
            'ceil': math.ceil, 'floor': math.floor, 'trunc': math.trunc,
            'pi': math.pi, 'e': math.e
        }
        log_event("CalculatorTool", {"event": "initialized"})
    
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
            safe_dict = {"__builtins__": {}}
            safe_dict.update(self.safe_functions)
            
            # Evaluate the expression
            result = eval(expression, safe_dict)
            
            log_event("CalculatorTool", {
                "event": "calculation_success",
                "expression": expression,
                "result": result
            })
            
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "formatted": f"{expression} = {result}"
            }
            
        except Exception as e:
            log_event("CalculatorTool", {
                "event": "calculation_error",
                "expression": expression,
                "error": str(e)
            })
            
            return {
                "success": False,
                "expression": expression,
                "error": str(e),
                "error_type": type(e).__name__
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
                "range": max(numbers) - min(numbers)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

calculator = CalculatorTool()
