from typing import List, Tuple
from mcp.types import Prompt, PromptMessage

from core.chat import Chat
from core.claude import Claude
from mcp_client import MCPClient


class CliChat(Chat):
    def __init__(
        self,
        doc_client: MCPClient,
        clients: dict[str, MCPClient],
        claude_service: Claude,
    ):
        super().__init__(clients=clients, claude_service=claude_service)
        self.doc_client: MCPClient = doc_client

    async def list_prompts(self) -> list[Prompt]:
        return await self.doc_client.list_prompts()

    async def list_docs_ids(self) -> list[str]:
        return await self.doc_client.read_resource("docs://documents")

    async def get_doc_content(self, doc_id: str) -> str:
        return await self.doc_client.read_resource(f"docs://documents/{doc_id}")

    async def get_prompt(
        self, command: str, doc_id: str
    ) -> list[PromptMessage]:
        return await self.doc_client.get_prompt(command, {"doc_id": doc_id})

    async def _extract_resources(self, query: str) -> str:
        mentions = [word[1:] for word in query.split() if word.startswith("@")]

        doc_ids = await self.list_docs_ids()
        mentioned_docs: list[Tuple[str, str]] = []

        for doc_id in doc_ids:
            if doc_id in mentions:
                content = await self.get_doc_content(doc_id)
                mentioned_docs.append((doc_id, content))

        return "".join(
            f'\n<document id="{doc_id}">\n{content}\n</document>\n'
            for doc_id, content in mentioned_docs
        )

    async def _process_command(self, query: str) -> bool:
        if not query.startswith("/"):
            return False

        words = query.split()
        command = words[0].replace("/", "")
        
        # Safe handling if no argument provided
        doc_arg = words[1] if len(words) > 1 else ""

        try:
            messages = await self.doc_client.get_prompt(
                command, {"doc_id": doc_arg}
            )
            # Use the helper to convert prompts to Gemini format
            self.messages += convert_prompt_messages_to_gemini(messages)
            return True
        except Exception as e:
            print(f"Error processing command: {e}")
            return False

    async def _process_query(self, query: str):
        if await self._process_command(query):
            return

        added_resources = await self._extract_resources(query)

        prompt = f"""
        The user has a question:
        <query>
        {query}
        </query>

        The following context may be useful in answering their question:
        <context>
        {added_resources}
        </context>

        Note the user's query might contain references to documents like "@report.docx". The "@" is only
        included as a way of mentioning the doc. The actual name of the document would be "report.docx".
        If the document content is included in this prompt, you don't need to use an additional tool to read the document.
        Answer the user's question directly and concisely. Start with the exact information they need. 
        Don't refer to or mention the provided context in any way - just use it to inform your answer.
        """

        # FIX: Use the service to add the message correctly (handles 'parts' vs 'content')
        self.claude_service.add_user_message(self.messages, prompt)


def convert_prompt_message_to_gemini(
    prompt_message: "PromptMessage",
) -> dict:
    # Gemini uses 'model' instead of 'assistant'
    role = "user" if prompt_message.role == "user" else "model"
    content = prompt_message.content
    
    text_content = ""

    # Handle various content shapes (string, dict, object)
    if isinstance(content, str):
        text_content = content
    elif hasattr(content, "text"):
        text_content = content.text
    elif isinstance(content, dict):
        text_content = content.get("text", "")
    elif isinstance(content, list):
         # Flatten list of blocks into one string
         for block in content:
             if isinstance(block, dict):
                 text_content += block.get("text", "")
             elif hasattr(block, "text"):
                 text_content += block.text

    # Gemini Format: {'role': '...', 'parts': ['...']}
    return {"role": role, "parts": [text_content]}


def convert_prompt_messages_to_gemini(
    prompt_messages: List[PromptMessage],
) -> List[dict]:
    return [
        convert_prompt_message_to_gemini(msg) for msg in prompt_messages
    ]