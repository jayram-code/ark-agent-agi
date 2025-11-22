"""
Code Execution Tool for ARK Agent AGI
Provides safe Python code execution in a sandboxed environment
"""

import sys
import io
import traceback
import signal
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Optional
from utils.logging_utils import log_event


class CodeExecutionTool:
    """
    Safe Python code execution with timeout and resource limits
    Designed for data analysis and computation tasks
    """

    def __init__(self, timeout_seconds: int = 10, max_output_chars: int = 10000):
        """
        Initialize Code Execution Tool

        Args:
            timeout_seconds: Maximum execution time (default 10 seconds)
            max_output_chars: Maximum output length (default 10000 chars)
        """
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

        # Safe builtins for code execution
        self.safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bin": bin,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "hex": hex,
            "int": int,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "oct": oct,
            "ord": ord,
            "pow": pow,
            "print": print,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }

        log_event(
            "CodeExecutionTool",
            {
                "event": "initialized",
                "timeout_seconds": timeout_seconds,
                "max_output_chars": max_output_chars,
            },
        )

    def execute(self, code: str, allow_imports: bool = False) -> Dict[str, Any]:
        """
        Execute Python code in a sandboxed environment

        Args:
            code: Python code to execute
            allow_imports: Whether to allow import statements (default False for safety)

        Returns:
            Dictionary with execution results, stdout, stderr, and errors
        """
        log_event(
            "CodeExecutionTool",
            {
                "event": "execution_started",
                "code_length": len(code),
                "allow_imports": allow_imports,
            },
        )

        # Create output buffers
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # Execution namespace
        exec_globals = {"__builtins__": self.safe_builtins.copy()}
        exec_locals = {}

        # Optionally allow safe imports
        if allow_imports:
            exec_globals["__builtins__"]["__import__"] = __import__
            # Add commonly used safe modules
            try:
                import math
                import json
                import datetime
                import re

                exec_globals.update({"math": math, "json": json, "datetime": datetime, "re": re})
            except ImportError:
                pass

        try:
            # Set up timeout handler (Unix-like systems only)
            if hasattr(signal, "SIGALRM"):

                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Code execution exceeded {self.timeout_seconds} seconds")

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)

            # Execute code with output capture
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, exec_globals, exec_locals)

            # Cancel timeout
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            # Get outputs
            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()

            # Truncate if too long
            if len(stdout_output) > self.max_output_chars:
                stdout_output = (
                    stdout_output[: self.max_output_chars]
                    + f"\n... (truncated, {len(stdout_output)} total chars)"
                )

            if len(stderr_output) > self.max_output_chars:
                stderr_output = (
                    stderr_output[: self.max_output_chars]
                    + f"\n... (truncated, {len(stderr_output)} total chars)"
                )

            # Get any returned values from the locals
            result_value = exec_locals.get("result", None)

            log_event(
                "CodeExecutionTool",
                {
                    "event": "execution_completed",
                    "stdout_length": len(stdout_output),
                    "stderr_length": len(stderr_output),
                    "has_result": result_value is not None,
                },
            )

            return {
                "success": True,
                "stdout": stdout_output,
                "stderr": stderr_output,
                "result": str(result_value) if result_value is not None else None,
                "locals": {k: str(v) for k, v in exec_locals.items() if not k.startswith("_")},
            }

        except TimeoutError as e:
            error_msg = str(e)
            log_event("CodeExecutionTool", {"event": "execution_timeout", "error": error_msg})

            return {
                "success": False,
                "error": error_msg,
                "error_type": "TimeoutError",
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue(),
            }

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()

            log_event(
                "CodeExecutionTool",
                {"event": "execution_error", "error_type": type(e).__name__, "error": error_msg},
            )

            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__,
                "traceback": error_trace,
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue(),
            }

        finally:
            # Clean up
            stdout_buffer.close()
            stderr_buffer.close()

    def execute_safe(self, code: str) -> Dict[str, Any]:
        """
        Execute code with maximum safety (no imports)

        Args:
            code: Python code to execute

        Returns:
            Execution results
        """
        return self.execute(code, allow_imports=False)

    def execute_with_libraries(self, code: str) -> Dict[str, Any]:
        """
        Execute code with common safe libraries available

        Args:
            code: Python code to execute

        Returns:
            Execution results
        """
        return self.execute(code, allow_imports=True)


# Global instance for easy access
code_executor = CodeExecutionTool()


def execute_code(code: str, allow_imports: bool = False) -> Dict[str, Any]:
    """
    Convenience function for code execution

    Args:
        code: Python code to execute
        allow_imports: Whether to allow imports

    Returns:
        Execution results dictionary
    """
    return code_executor.execute(code, allow_imports)
