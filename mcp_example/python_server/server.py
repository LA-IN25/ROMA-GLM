#!/usr/bin/env python3
"""
Example MCP Server using the Python SDK
This server provides basic tools and resources for demonstration
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetResourceRequest,
    GetResourceResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
    Resource,
)

# Create the server instance
server = Server("example-mcp-server")

# Register tools
@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="calculate",
                description="Perform basic math calculations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
                        }
                    },
                    "required": ["expression"]
                }
            ),
            Tool(
                name="get_weather",
                description="Get mock weather information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        }
                    },
                    "required": ["location"]
                }
            ),
            Tool(
                name="generate_uuid",
                description="Generate a random UUID",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> CallToolResult:
    """Handle tool calls"""

    if name == "calculate":
        expression = arguments.get("expression", "")
        try:
            # Safe evaluation of basic math expressions
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")

            result = eval(expression)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Result: {expression} = {result}"
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error calculating '{expression}': {str(e)}"
                    )
                ],
                isError=True
            )

    elif name == "get_weather":
        location = arguments.get("location", "Unknown")
        # Mock weather data
        weather_data = {
            "New York": {"temp": "72°F", "condition": "Sunny"},
            "London": {"temp": "59°F", "condition": "Cloudy"},
            "Tokyo": {"temp": "68°F", "condition": "Clear"},
            "Paris": {"temp": "64°F", "condition": "Rainy"},
        }

        weather = weather_data.get(location, {"temp": "70°F", "condition": "Unknown"})
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Weather in {location}: {weather['temp']}, {weather['condition']}"
                )
            ]
        )

    elif name == "generate_uuid":
        import uuid
        generated_uuid = str(uuid.uuid4())
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Generated UUID: {generated_uuid}"
                )
            ]
        )

    else:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )
            ],
            isError=True
        )

# Register resources
@server.list_resources()
async def handle_list_resources() -> ListResourcesResult:
    """List available resources"""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="example://config",
                name="Server Configuration",
                description="Current server configuration and settings",
                mimeType="application/json"
            ),
            Resource(
                uri="example://status",
                name="Server Status",
                description="Current server status and health information",
                mimeType="application/json"
            )
        ]
    )

@server.get_resource()
async def handle_get_resource(uri: str) -> GetResourceResult:
    """Get resource content"""

    if uri == "example://config":
        config = {
            "server_name": "example-mcp-server",
            "version": "1.0.0",
            "capabilities": ["tools", "resources"],
            "tools_available": ["calculate", "get_weather", "generate_uuid"],
            "resources_available": ["config", "status"]
        }
        return GetResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(config, indent=2)
                )
            ]
        )

    elif uri == "example://status":
        import datetime
        import psutil

        status = {
            "status": "running",
            "uptime": datetime.datetime.now().isoformat(),
            "memory_usage": f"{psutil.virtual_memory().percent}%",
            "cpu_usage": f"{psutil.cpu_percent()}%",
            "active_connections": 1
        }
        return GetResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(status, indent=2)
                )
            ]
        )

    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main server entry point"""
    # Run the server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="example-mcp-server",
                server_version="1.0.0",
                capabilities={
                    "tools": {},
                    "resources": {}
                }
            )
        )

if __name__ == "__main__":
    print("Starting MCP Server...")
    asyncio.run(main())
```

<file_path>
ROMA-QWEN-ARCH/mcp_example/python_server/requirements.txt</file_path>
<edit_description>
Create requirements file for the Python MCP server</edit_description></think>
<think></think>
```python
# MCP Server Dependencies
mcp>=1.0.0
psutil>=5.9.0
```

<file_path>
ROMA-QWEN-ARCH/mcp_example/python_server/README.md</file_path>
<edit_description>
Create README for the Python MCP server example</edit_description></think>
<think></think>
```python
# Python MCP Server Example

This is an example MCP server built using the Python SDK that demonstrates basic functionality.

## Features

### Tools
- **calculate**: Perform basic math calculations
- **get_weather**: Get mock weather information
- **generate_uuid**: Generate random UUIDs

### Resources
- **example://config**: Server configuration information
- **example://status**: Server status and health metrics

## Installation & Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python server.py
   ```

## Usage in Zed

To use this custom MCP server in Zed:

1. **Add to your Zed settings** (`~/.config/zed/settings.json`):

```json
{
  "context_servers": {
    "my-python-server": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_example/python_server/server.py"],
      "cwd": "/absolute/path/to/mcp_example/python_server"
    }
  }
}
```

2. **Restart Zed** to load the new server

3. **Access the tools** via Zed's AI assistant or command palette

## Development

This server demonstrates:
- Tool registration and handling
- Resource management
- Error handling
- Basic MCP protocol implementation

## Extend

To add more functionality:
1. Add new tools in the `@server.list_tools()` handler
2. Implement tool logic in `@server.call_tool()` handler
3. Add resources in `@server.list_resources()` and `@server.get_resource()` handlers
```

Now let me show you how to connect this custom server to Zed:
<tool_call>create_directory
<arg_key>path</arg_key>
<arg_value>/home/LAIN/ROMA-QWEN-ARCH/mcp_example/typescript_server</arg_value>
</tool_call>
