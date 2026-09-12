# This file tests that the Computer Use Agent tools are correctly
# registered as LangChain tools and expose the expected names.

from computer.tools import (
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text
)

tools = [
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text
]

for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print()