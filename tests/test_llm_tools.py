# This file tests whether the groq LLM can see the Computer Use Agent tools
# and select an appropriate tool for a user's request.

from computer.llm import create_llm

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

llm = create_llm()

llm_with_tools = llm.bind_tools(tools)

response = llm_with_tools.invoke(
    "Open Notepad on my computer."
)

print("LLM response:")
print(response)

print("\nTool calls:")

if response.tool_calls: #response.tool_calls is a built-in property
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call['name']}")
        print(f"Arguments: {tool_call['args']}")
        print()

else:
    print("No tool was selected.")