from typing import List, Dict, Any, Callable, Optional
from pydantic import BaseModel
import inspect

class AITool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    function: Optional[Callable] = None  # The actual python function to execute

    class Config:
        arbitrary_types_allowed = True

def format_tool_for_openai(tool: AITool) -> Dict[str, Any]:
    """Formats a tool for OpenAI API"""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    }

def format_tool_for_anthropic(tool: AITool) -> Dict[str, Any]:
    """Formats a tool for Anthropic API"""
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters
    }
