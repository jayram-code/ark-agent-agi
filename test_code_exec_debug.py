import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.code_execution_tool import code_executor

# Test the simple case
code = "result = 2 + 2\\nprint(result)"
result = code_executor.execute(code, allow_imports=False)

print(f"Success: {result['success']}")
if result['success']:
    print(f"Stdout: {result['stdout']}")
else:
    print(f"Error: {result.get('error', 'Unknown')}")
    print(f"Error Type: {result.get('error_type', 'Unknown')}")
    if 'traceback' in result:
        print(f"Traceback:\n{result['traceback']}")
