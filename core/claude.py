import os
import google.generativeai as genai
from google.generativeai.types import content_types
from collections.abc import Iterable

class Claude:
    def __init__(self, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model)

    def add_user_message(self, messages: list, message):
        # Gemini expects simple string parts for user text
        content = message
        if isinstance(message, list):
            content = ""
            for block in message:
                 if isinstance(block, dict) and block.get("type") == "text":
                     content += block.get("text", "") + "\n"
        
        messages.append({"role": "user", "parts": [str(content)]})

    def add_assistant_message(self, messages: list, response):
        # We store the raw Gemini response object or a dict reconstruction
        if response.parts:
            messages.append(response)

    def add_tool_output_messages(self, messages: list, tool_outputs: list):
        # Gemini expects tool outputs in a 'function_response' part
        # The tool_outputs passed here will be properly formatted from tools.py
        messages.append({
            "role": "function",
            "parts": tool_outputs
        })

    def text_from_message(self, response):
        try:
            return response.text
        except ValueError:
            # Sometimes response is just a function call with no text
            return ""

    def chat(
        self,
        messages: list,
        system: str = None,
        tools: list = None,
    ):
        # Configure the model with tools if present
        # Note: In a real app, we should instantiate the model once with tools, 
        # but for this stateless loop, we re-instantiate or pass tools to generate_content
        
        # We need to use a fresh model object if we are changing tools dynamically
        current_model = self.model
        if tools:
            current_model = genai.GenerativeModel(
                self.model.model_name, 
                tools=[tools], # Gemini expects a list of tool lists/functions
                system_instruction=system
            )
        elif system:
             current_model = genai.GenerativeModel(
                self.model.model_name, 
                system_instruction=system
            )

        response = current_model.generate_content(
            messages,
            request_options={"timeout": 600}
        )
        return response