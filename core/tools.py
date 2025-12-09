import json
from typing import Optional, Literal, List, Any
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient

class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        """Gets all tools and formats them for OpenAI function calling."""
        openai_tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            for t in tool_models:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema  # MCP schema maps directly to parameters
                    }
                })
        return openai_tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        """Finds the first client that has the specified tool."""
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], message: Any
    ) -> List[dict]:
        """
        Executes tool calls from an OpenAI response message.
        Returns a list of messages with role='tool'.
        """
        if not message.tool_calls:
            return []

        tool_result_messages = []
        
        for tool_call in message.tool_calls:
            tool_use_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args_json = tool_call.function.arguments
            
            # Parse arguments
            try:
                tool_input = json.loads(tool_args_json)
            except json.JSONDecodeError:
                tool_input = {}

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            content_result = ""
            is_error = False

            if not client:
                content_result = "Could not find that tool"
                is_error = True
            else:
                try:
                    tool_output: CallToolResult | None = await client.call_tool(
                        tool_name, tool_input
                    )
                    items = []
                    if tool_output:
                        items = tool_output.content
                    
                    # Extract text from content items
                    content_list = [
                        item.text for item in items if isinstance(item, TextContent)
                    ]
                    content_result = json.dumps(content_list)
                    is_error = tool_output.isError if tool_output else False
                    
                except Exception as e:
                    content_result = json.dumps({"error": f"Error executing tool '{tool_name}': {e}"})
                    is_error = True

            # OpenAI expects the result in a message with role='tool'
            tool_result_messages.append({
                "role": "tool",
                "tool_call_id": tool_use_id,
                "content": content_result
            })

        return tool_result_messages