import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.code_execution_tool import code_executor

code = "result = 2 + 2\\nprint(result)"
result = code_executor.execute(code, allow_imports=False)

print(f"Success: {result['success']}")
print(f"Result keys: {result.keys()}")
if not result['success']:
    print(f"Error: {result.get('error')}")
    print(f"Error type: {result.get('error_type')}")
    print(f"Traceback: {result.get('traceback')}")
else:
    print(f"Stdout: {result['stdout']}")
