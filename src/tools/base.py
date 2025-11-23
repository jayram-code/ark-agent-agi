from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    """
    name: str
    description: str

    def __init__(self, name: str = None, description: str = None):
        if name:
            self.name = name
        if description:
            self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the given arguments.
        """
        pass

    @property
    def schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for the tool's arguments (for LLM function calling).
        Default implementation can be overridden or inferred.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
