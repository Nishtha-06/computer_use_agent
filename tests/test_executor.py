# This file tests whether a tool call selected by the LLM can be
# execute by the compputer Use Agent

from computer.llm import create_llm
from computer.tools import (
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text,
)

from computer.executor import execute_tool

# List all tools available to the LLM.
tools = [
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text,
]

#create Groq LLM
llm = create_llm()

# Bind the computer tools to the llm
llm_with_tools = llm.bind_tools(tools)

# Ask the LLM to perform a compuetr task.
response = llm_with_tools.invoke(
    "Open Notepad on my computer."
)

print("LLM selected:")

if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call['name']}")
        print(f"Arguments: {tool_call['args']}")

        # execute the tool selected by LLM
        result = execute_tool(tool_call)

        print("Tool executed successfully.")
        print(f"Result: {result}")

else:
    print("No tool was selected")