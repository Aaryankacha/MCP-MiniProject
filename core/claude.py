import os
from openai import OpenAI
from typing import List, Optional, Any

class Claude:
    def __init__(self, model: str = "gpt-4o"):
        # Ensure OPENAI_API_KEY is in your .env
        self.client = OpenAI()
        self.model = model

    def add_user_message(self, messages: list, message):
        """Adds a user message to history. Handles both strings and list of blocks."""
        content = message
        # If it's a list (previously Anthropic blocks), join the text parts
        if isinstance(message, list):
            content = ""
            for block in message:
                if isinstance(block, dict) and block.get("type") == "text":
                    content += block.get("text", "") + "\n"
        
        # OpenAI expects a simple string for content usually, unless using vision.
        messages.append({"role": "user", "content": str(content)})

    def add_assistant_message(self, messages: list, message):
        """Adds the assistant's response to history."""
        # OpenAI returns an object, we need to convert it to a dict for the history
        msg_dict = {
            "role": "assistant",
            "content": message.content
        }
        if message.tool_calls:
            msg_dict["tool_calls"] = message.tool_calls
        
        messages.append(msg_dict)

    def add_tool_output_messages(self, messages: list, tool_outputs: list):
        """Specific helper for OpenAI tool outputs."""
        messages.extend(tool_outputs)

    def text_from_message(self, message):
        """Extracts text content from the response object."""
        return message.content if message.content else ""

    def chat(
        self,
        messages: List[dict],
        system: Optional[str] = None,
        temperature: float = 1.0,
        stop_sequences: List[str] = [],
        tools: Optional[List[dict]] = None,
        thinking: bool = False, # OpenAI doesn't support 'thinking' param yet
        thinking_budget: int = 1024,
    ):
        # Prepare messages
        final_messages = messages.copy()
        
        # Handle system prompt (OpenAI expects it as the first message)
        if system:
            final_messages.insert(0, {"role": "system", "content": system})

        params = {
            "model": self.model,
            "messages": final_messages,
            "temperature": temperature,
        }

        if stop_sequences:
            params["stop"] = stop_sequences

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message