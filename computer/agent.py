# this file contains the basic computer use agent that connects the
# user's goal, the groq LLM,computer tools and tool execution.

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
from computer.observer import capture_screen,save_screenshot

class ComputerUseAgent:
    """Computer Use Agent that can execute a tool and observe the result"""

    def __init__(self):
        """Initialize the LLM and available computer tools."""

        self.tools = [
            tool_screenshot,
            tool_open_application,
            tool_open_url,
            tool_move_mouse,
            tool_click,
            tool_press_key,
            tool_type_text,
        ]

        self.llm = create_llm()
        self.llm_with_tools = self.llm.bind_tools(self.tools) # bind_tools() is a built-in LangChain method

    def run(self,goal):
        """Execute the first action selected by the LLM and observe the result."""

        # Ask the LLM to decide which computer action is required.
        response = self.llm_with_tools.invoke(goal)

        if not response.tool_calls:
            return {
                "status":"no_tool",
                "response":response.content
            }

        results = []

        # Execute each tool selected by the LLM.
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call)

            results.append({
                "tool":tool_call["name"],
                "arguments":tool_call["args"],
                "result":result
            })

        # capture the computer state after executing the action.
        image = capture_screen()

        # save the observation for inspection.
        screenshot_path = save_screenshot(image)

        return {
            "status":"executed",
            "results":results,
            "screenshot":str(screenshot_path)
        }