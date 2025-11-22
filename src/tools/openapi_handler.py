import asyncio
import json
from typing import Any, Callable, Dict


class OpenAPIHandler:
    """Parses OpenAPI specs and creates callable tools."""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def load_spec(self, spec_path: str):
        """Load an OpenAPI spec and register tools."""
        with open(spec_path, "r") as f:
            spec = json.load(f)

        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                operation_id = details.get("operationId")
                if operation_id:
                    self.register_tool(operation_id, self.create_mock_tool(operation_id))

    def register_tool(self, name: str, func: Callable):
        self.tools[name] = func

    def create_mock_tool(self, operation_id: str) -> Callable:
        """Create a mock tool function based on operation ID."""

        async def mock_tool(**kwargs):
            await asyncio.sleep(0.1)
            if "weather" in operation_id:
                return {"temperature": 72, "condition": "Sunny", "location": kwargs.get("location")}
            return {"status": "success", "data": kwargs}

        return mock_tool

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        if tool_name in self.tools:
            return await self.tools[tool_name](**kwargs)
        raise ValueError(f"Tool {tool_name} not found")


# Global handler
openapi_handler = OpenAPIHandler()
