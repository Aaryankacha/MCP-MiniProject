import os
import google.generativeai as genai
from google.generativeai.types import content_types
from collections.abc import Iterable

class Claude:
    def __init__(self, model: str = "gemini-flash-latest"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model)

    def add_user_message(self, messages: list, message):
        content = message
        if isinstance(message, list):
            content = ""
            for block in message:
                 if isinstance(block, dict) and block.get("type") == "text":
                     content += block.get("text", "") + "\n"
        
        # Store as a clean dictionary
        messages.append({"role": "user", "parts": [str(content)]})

    def add_assistant_message(self, messages: list, response):
        # FIX: Extract the actual parts from the response object
        # and store them as a simple dictionary.
        try:
            if hasattr(response, 'parts') and response.parts:
                clean_parts = []
                for part in response.parts:
                    if part.text:
                        clean_parts.append({"text": part.text})
                    elif part.function_call:
                        clean_parts.append({
                            "function_call": {
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args)
                            }
                        })
                
                if clean_parts:
                    messages.append({
                        "role": "model",
                        "parts": clean_parts
                    })
        except Exception as e:
            print(f"Warning: Failed to add assistant message: {e}")

    def add_tool_output_messages(self, messages: list, tool_outputs: list):
        messages.append({
            "role": "function",
            "parts": tool_outputs
        })

    def text_from_message(self, response):
        try:
            return response.text
        except ValueError:
            return ""

    def chat(self, messages: list, system: str = None, tools: list = None):
        current_model = self.model
        if tools:
            current_model = genai.GenerativeModel(
                self.model.model_name, 
                tools=[tools], 
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