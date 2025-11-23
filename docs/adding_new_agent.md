# How to Add a New Agent or Tool

This guide explains how to extend ARK Agent AGI by adding new specialized agents or tools.

## 1. Adding a New Agent

### Step 1: Create the Agent Class
Create a new file in `src/agents/` (e.g., `my_new_agent.py`). Inherit from `BaseAgent`.

```python
from agents.base_agent import BaseAgent
from models.messages import AgentMessage

class MyNewAgent(BaseAgent):
    def __init__(self, agent_id: str, orchestrator):
        super().__init__(agent_id, orchestrator)
        self.system_prompt = "You are a helpful assistant for..."

    async def process_request(self, message: AgentMessage) -> AgentMessage:
        # 1. Extract payload
        user_text = message.payload.get("text")
        
        # 2. Use LLM or logic
        response_text = await self.call_llm(user_text)
        
        # 3. Return response
        return self.create_response(
            target_agent=message.sender,
            payload={"text": response_text}
        )
```

### Step 2: Register the Agent
Update `src/core/orchestrator.py` (or your bootstrap script) to register the new agent.

```python
# In orchestrator setup
from agents.my_new_agent import MyNewAgent
orchestrator.register_agent("my_new_agent", MyNewAgent("my_new_agent", orchestrator))
```

### Step 3: Update Routing Policy
If you want the Orchestrator to route messages to this agent automatically, update `src/policies/routing_policy.py`.

```python
# In RoutingPolicy.__init__
self.keyword_rules["my_keyword"] = "my_new_agent"
self.intent_rules["my_intent"] = "my_new_agent"
```

---

## 2. Adding a New Tool

### Step 1: Create the Tool Class
Create a new file in `src/tools/` (e.g., `my_tool.py`). Inherit from `BaseTool`.

```python
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        }
    }

    def execute(self, param1: str) -> str:
        # Implementation logic
        return f"Processed {param1}"
```

### Step 2: Give Tool to an Agent
In your agent's `__init__` method, add the tool to `self.tools`.

```python
from tools.my_tool import MyTool

class MyNewAgent(BaseAgent):
    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        self.tools = [MyTool()]
```

### Step 3: Update System Prompt
Tell the agent about the tool in its system prompt so it knows when to use it.

```python
self.system_prompt += "\nYou have access to 'my_tool'. Use it when..."
```
