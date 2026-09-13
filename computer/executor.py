# this file execute the computer controll tool selected by the LLM.
# It receives a structured tool call and run the matching LangChain tool.

from computer.permissions import requires_permission

from computer.tools import (
    tool_screenshot,
    tool_open_application,
    tool_open_url,
    tool_move_mouse,
    tool_click,
    tool_press_key,
    tool_type_text
)

#Map each tool name to its actual Langhain tool.
TOOL_MAP = {
    "tool_screenshot": tool_screenshot,
    "tool_open_application": tool_open_application,
    "tool_open_url": tool_open_url,
    "tool_move_mouse": tool_move_mouse,
    "tool_click": tool_click,
    "tool_press_key": tool_press_key,
    "tool_type_text": tool_type_text,
}

def execute_tool(tool_call):
    """Check permission and execute one tool call returned by LLM."""
    tool_name = tool_call["name"]
    tool_args = tool_call['args']

    # Check whether this action requires user approval.
    if requires_permission(tool_name):
        print(f"\nPermission required for: {tool_name}")
        print(f"Arguments: {tool_args}")

        approval = input("Allow this action? (y/n): ").strip().lower()
        if approval != "y":
            print("Action denied by user.")
            return {
                "status": "denied",
                "tool": tool_name,
            }
        
    # Find the corresponding LangChain tool.
    selected_tool = TOOL_MAP.get(tool_name)

    if selected_tool is None:
        raise ValueError(f"Unknown tool:{tool_name}")

    # Execute the selected tool with the arguments choosen by the LLM
    result = selected_tool.invoke(tool_args)

    return result
