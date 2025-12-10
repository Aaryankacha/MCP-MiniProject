from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager

class Chat:
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list = []

    async def _process_query(self, query: str):
        self.claude_service.add_user_message(self.messages, query)

    def _is_tool_call(self, response):
        """Helper to check if Gemini wants to call a function"""
        try:
            return bool(response.parts and response.parts[0].function_call)
        except:
            return False

    async def run(self, query: str) -> str:
        final_text_response = ""
        await self._process_query(query)

        while True:
            # 1. Get response from Gemini
            tools = await ToolManager.get_all_tools(self.clients)
            response = self.claude_service.chat(
                messages=self.messages,
                tools=tools,
            )

            # 2. Add the assistant's response to history
            self.claude_service.add_assistant_message(self.messages, response)

            # 3. Check for tool usage
            if self._is_tool_call(response):
                print(" > Executing tool...")
                
                # Execute tools and get the response parts
                tool_outputs = await ToolManager.execute_tool_requests(
                    self.clients, response
                )

                # Add the tool outputs to history
                self.claude_service.add_tool_output_messages(
                    self.messages, tool_outputs
                )
                # Loop continues to send tool outputs back to the model
            else:
                # No tool calls, we are done
                final_text_response = self.claude_service.text_from_message(response)
                break

        return final_text_response