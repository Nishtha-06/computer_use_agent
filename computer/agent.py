# this file contains the basic computer use agent that connects the
# user's goal, the groq LLM,computer tools and tool execution.

import base64
from io import BytesIO

import time

from computer.audit import log_action

from computer.llm import create_vision_llm
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
    """Computer Use Agent that observes the screen and executes actions."""

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

        self.llm = create_vision_llm()
        self.llm_with_tools = self.llm.bind_tools(self.tools) # bind_tools() is a built-in LangChain method

    def image_to_base64(self,image):
        """Convert a screenshot into Base64 encoded PNG data."""

        buffer = BytesIO()
        image.save(buffer,format="PNG")

        image_bytes = buffer.getvalue()

        return base64.b64encode(image_bytes).decode("utf-8")

    def ask_vision_model(self,goal,image,action_history):
        """Ask the vision model to choose the next action.
        based on the current screen ans actions already performed."""

        image_base64 = self.image_to_base64(image)

        # convert the action history into readable text for the model.
        if action_history:
            history_text = ""
            for item in action_history:
                history_text += f"{item['tool']}({item['arguments']})\n"

        else:
            history_text = "No actions have been performed yet."

        response = self.llm_with_tools.invoke(
            [
                {
                    "role":"user",
                    "content":[
                        {
                            "type":"text",
                            "text":(
                                f"User goal: {goal}\n\n"
                                f"Actions already performed:\n{history_text}\n\n"
                                "Look at the current computer screenshot. "
                                "Decide the next computer action required "
                                "to make progress toward the user's goal."
                                "Choose an availble tool."
                                "Important rules:\n"
                                "1.Do not repeat an action that has already "
                                "succeeded unless the screenshot shows that it "
                                "needs to be repeated.\n"
                                "2.Consider what has alreday been completd.\n"
                                "3.Choose only one next computer action.\n"
                                "Continue with the remianing task."
                            ),
                        },{
                            "type":"image_url",
                            "image_url":{
                                "url":f"data:image/png;base64,{image_base64}",
                            },
                        },
                    ]
                }
            ]
        )
        return response

    def verify_task(self,goal,image):
        """Ask the vision whether the user's goal has been completed."""

        image_base64 = self.image_to_base64(image)

        response = self.llm.bind(max_tokens=50).invoke(
            [
                {
                    "role":"user",
                    "content":[
                        {
                            "type":"text",
                            "text":(
                                f"User goal: {goal}\n\n"
                                "Look at the current computer screenshot and verify the ACTUAL "
                                "computer state.\n\n"
                                "Do not use text shown in VS Code, terminals, browsers, ChatGPT, "
                                "or previous conversation output as evidence that the task is complete.\n\n"
                                "Only consider the actual application window involved in the task.\n\n"
                                "The goal is complete only if every part of the user's goal has "
                                "actually been performed on the computer.\n\n"
                                "At the very end of your response, write exactly one of:\n"
                                "VERDICT=YES\n"
                                "VERDICT=NO"
                            )
                        },
                        {
                            "type":"image_url",
                            "image_url":{
                                "url":f"data:image/png;base64,{image_base64}",
                            }
                        }
                    ]
                }
            ]
        )

        return response.content

    def run(self,goal,max_steps=5):
        """Run the computer use loop for a limited number of steps. """

        results = []

        #store actions that have been executed.
        action_history = []

        # Track how many times the agent has failed verification.
        failed_attempts = 0

        # Take the initial screenshot before deciding what to do.
        image = capture_screen()

        for step in range(max_steps):
            print(f"\n--- Step {step + 1}---")

            # Ask the vision model to choose the next action.
            response = self.ask_vision_model(goal,image,action_history)

            print("Model response:")
            print(response.content)

            print("Tool calls:")
            print(response.tool_calls)

            if not response.tool_calls:
                # The model did not select an action.
                # This does not automatically mean the task is complete.
                print("No tool selected.")

                # verify the actual computer state.
                image = capture_screen()

                verification = self.verify_task(goal,image)

                print(f"Verification: {verification}")

                if "VERDICT=YES" in verification.upper():
                    return {
                        "status":"completed",
                        "results":results,
                    }

                print("Task is not complete, but the model selected no action.")

                return {
                    "status":"no_action",
                    "results":results
                }

                return {
                    "status":"completed",
                    "results":results
                }

            # Execute the tools selected by the model
            for tool_call in response.tool_calls:
                print(f"Selected tool: {tool_call['name']}")
                print(f"Arguments: {tool_call['args']}")
    
                result = execute_tool(tool_call)

                # stop this execution cycle if the user denied the action.
                if isinstance(result,dict) and result.get("status") == "denied":
                    return{
                        "status":"permission_denied",
                        "results":results,
                    }

                # return the executed action in the audit log.
                log_action(
                    tool_call["name"],
                    tool_call["args"],
                    result,

                )

                results.append(
                    {
                        "step":step+1,
                        "tool":tool_call["name"],
                        "arguments":tool_call["args"],
                        "result":result,
                    }
                )

                # Record the action for the next LLM decision.
                action_history.append(
                    {
                        "tool":tool_call["name"],
                        "arguments":tool_call["args"],
                    }
                )

                # Give the application time to open or respond.
                time.sleep(2)

                # Observe the computer again after executing the action.
                image = capture_screen()

                # verify whether the user's goal has been completed.
                verification = self.verify_task(goal,image)

                print(f"Verification: {verification}")

                if "VERDICT=YES" in verification.upper():
                    return{
                        "status":"completed",
                        "results":results
                    }

                failed_attempts += 1
                print(f"Task not completed. Failed attempts: {failed_attempts}")

                # Stop if the agent repeatedly fails to make progress.
                if failed_attempts >= 3:
                    return {
                        "status": "failed",
                        "results": results,
                    }

        return {
            "status":"max_steps_reached",
            "results":results,
        }
