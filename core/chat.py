from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager

class Chat:
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[dict] = [] # Changed type hint to simple dict

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            # 1. Get response from OpenAI
            response = self.claude_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            # 2. Add the assistant's response (text or tool call) to history
            self.claude_service.add_assistant_message(self.messages, response)

            # 3. Check if the model wants to call tools
            if response.tool_calls:
                print("Tool call detected...")
                
                # Execute tools and get the 'tool' role messages back
                tool_result_messages = await ToolManager.execute_tool_requests(
                    self.clients, response
                )

                # Add the tool outputs to history
                self.claude_service.add_tool_output_messages(
                    self.messages, tool_result_messages
                )
                
                # Loop continues to send tool outputs back to the model
            else:
                # No tool calls, we are done
                final_text_response = self.claude_service.text_from_message(
                    response
                )
                break

        return final_text_response