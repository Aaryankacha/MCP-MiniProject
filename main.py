import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.claude import Claude

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# OpenAI Config (Swapped from Anthropic)
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
openai_api_key = os.getenv("OPENAI_API_KEY", "")

# Validation
assert openai_api_key, (
    "Error: OPENAI_API_KEY cannot be empty. Update .env"
)

async def main():
    # Initialize our OpenAI wrapper
    claude_service = Claude(model=openai_model)

    server_scripts = sys.argv[1:]
    clients = {}

    # Determine command based on environment (uv or python)
    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        # 1. Connect to the Document MCP Server
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        # 2. Connect to any additional servers passed as arguments
        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        # 3. Initialize Chat Logic
        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=claude_service,
        )

        # 4. Run CLI Interface
        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())