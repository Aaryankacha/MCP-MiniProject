import json
from typing import Optional, List, Any
from mcp.types import CallToolResult, TextContent
from mcp_client import MCPClient
from google.protobuf import struct_pb2

class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        """Gets all tools and formats them for Gemini."""
        gemini_tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            for t in tool_models:
                # Gemini FunctionDeclaration format
                gemini_tools.append({
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema # MCP schema maps directly
                })
        return gemini_tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        for client in clients:
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], response: Any
    ) -> List[dict]:
        """
        Executes function calls from a Gemini response.
        Returns a list of 'function_response' parts.
        """
        # Check if the first part is a function call
        if not response.parts:
            return []
            
        function_calls = []
        for part in response.parts:
            if fn := part.function_call:
                function_calls.append(fn)

        if not function_calls:
            return []

        tool_result_parts = []
        
        for fn in function_calls:
            tool_name = fn.name
            # Convert MapComposite to dict
            tool_args = dict(fn.args)

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            result_content = {}
            
            if not client:
                result_content = {"error": "Tool not found"}
            else:
                try:
                    tool_output: CallToolResult | None = await client.call_tool(
                        tool_name, tool_args
                    )
                    
                    # Extract text content
                    texts = []
                    if tool_output and tool_output.content:
                        texts = [item.text for item in tool_output.content if isinstance(item, TextContent)]
                    
                    result_content = {"result": "\n".join(texts)}
                    
                except Exception as e:
                    result_content = {"error": str(e)}

            # Build the Gemini FunctionResponse part
            # It requires 'name' and 'response' (which must be a dict)
            tool_result_parts.append({
                "function_response": {
                    "name": tool_name,
                    "response": result_content
                }
            })

        return tool_result_parts