# 🔌 OpenAPI Tools Integration

Ark Agent AGI supports dynamic tool execution using **OpenAPI Specifications**. This allows agents to interact with any external API that provides a standard OpenAPI (Swagger) spec.

## How it Works

1.  **Load Spec**: The `OpenAPIHandler` parses a JSON/YAML spec file.
2.  **Register Tools**: Each operation in the spec is converted into a callable tool.
3.  **Execute**: Agents (like `ActionExecutorAgent`) can invoke these tools by name.

## Adding a New Tool

1.  Place your `openapi.json` file in `src/tools/`.
2.  Update `src/tools/openapi_handler.py` to load the new spec.
3.  The tools will be automatically available to agents.

## Example Spec

```json
{
  "paths": {
    "/weather": {
      "get": {
        "operationId": "get_current_weather",
        ...
      }
    }
  }
}
```

This creates a tool named `get_current_weather` that agents can call.
