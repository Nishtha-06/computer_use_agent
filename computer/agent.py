# this file contains the basic computer use agent that connects the
# user's goal, the groq LLM,computer tools and tool execution.

import base64
from io import BytesIO

import time

from computer.planner import TaskPlanner
from computer.audit import log_action
from computer.retry import RetryManager

from computer.task_state import TaskState
from computer.task_context import TaskContext
from computer.retry import RetryManager

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
from computer.retry import RetryManager

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
        self.planner = TaskPlanner()
        self.retry_manager = RetryManager()

    def image_to_base64(self,image):
        """Convert a screenshot into Base64 encoded PNG data."""

        buffer = BytesIO()
        image.save(buffer,format="PNG")

        image_bytes = buffer.getvalue()

        return base64.b64encode(image_bytes).decode("utf-8")

    def ask_vision_model(self,goal,image,action_history,plan):
        """Ask the vision model to choose the next action.
        based on the current screen ans actions already performed."""

        image_base64 = self.image_to_base64(image)

        # convert the action history into readable text for the model.
        if action_history:
            history_text = ""
            for item in action_history:
                history_text += (
                    f"{item['tool']}({item['arguments']})\n"
                    f"[status: {item.get('verification','unknown')}]\n"
                    )

        else:
            history_text = "No actions have been performed yet."

        response = self.llm_with_tools.bind(reasoning_effort="none").invoke(
            [
                {
                    "role":"user",
                    "content":[
                        {
                            "type":"text",
                            "text":(
                                f"User goal: {goal}\n\n"
                                f"Task plan:\n{plan}\n\n"
                                f"Actions already performed:\n{history_text}\n\n"
                                "Action selection rules:\n"
                                "1. Prefer direct tools over mouse clicks whenever a direct tool exists.\n"
                                "2. To open an application, ALWAYS use tool_open_application.\n"
                                "3. To open a URL, ALWAYS use tool_open_url.\n"
                                "4. NEVER click a taskbar icon or desktop application icon when "
                                "a direct tool_open_application call can open the application.\n"
                                "5. NEVER manually click the browser or type a URL when "
                                "tool_open_url can open the requested URL directly.\n"
                                "6. Use tool_click only for UI interactions that cannot be "
                                "performed by another available tool.\n"
                                "7. Do not guess coordinates for actions that have a direct tool.\n"
                                "8. Do not repeat an action that already succeeded.\n"
                                "9. Choose exactly ONE next action.\n"
                                "10. If the task is already complete, do not select another tool.\n"
                                "11. Treat actions marked as failed as unsuccessful attempts.\n"
                                "12. Use the current screenshot together with the action history "
                                "to decide the next action.\n"
                                "13. Do not click the taskbar to interact with an application that is already open."
                                "14. After opening an application, inspect the screenshot before deciding whether another action is necessary."
                                "15. If the required application is already visible and usable, interact with it directly rather than reopening or selecting it from the taskbar."
                                "16. A status of 'executed_goal_incomplete' means that action succeeded — "
                                "do not repeat it. Build on the resulting screen state instead.\n"
                                "17. If the application required by the goal is already visible and open "
                                "18. The current screenshot is already provided to you. Do not call "
                                "tool_screenshot just to inspect the current screen again.\n"
                                "19. If the previous action was tool_open_application and it succeeded, "
                                "and the task requires entering text into that application, select "
                                "tool_type_text with the exact text required by the user's goal.\n"
                                "20. When selecting tool_type_text, never use null or None for the text "
                                "argument. Extract the exact text that the user wants typed from the goal "
                                "or task plan.\n"
                                "in the current screenshot, do NOT call tool_open_application again. "
                                "Interact with what's already on screen (click, type, or navigate) instead."
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

    # def verify_task(self,goal,image):
    #     """Ask the vision whether the user's goal has been completed."""

    #     image_base64 = self.image_to_base64(image)

    #     response = self.llm.bind(max_tokens=50).invoke(
    #         [
    #             {
    #                 "role":"user",
    #                 "content":[
    #                     {
    #                         "type":"text",
    #                         "text":(
    #                             # f"User goal: {goal}\n\n"
    #                             # "Look at the current computer screenshot and verify the ACTUAL "
    #                             # "computer state.\n\n"
    #                             # "ACTUAL computer state.\n\n"
    #                             # "Do not use text shown in VS Code, terminals, browsers, "
    #                             # "ChatGPT, or previous conversation output as evidence "
    #                             # "that the task is complete.\n\n"
    #                             # "Only consider the actual application window involved "
    #                             # "in the task.\n\n"
    #                             # "The goal is complete only if every part of the user's "
    #                             # "goal has actually been performed on the computer.\n\n"
    #                             # "Return exactly one line:\n"
    #                             # "VERDICT=YES\n"
    #                             # "VERDICT=NO"
    #                             f"User goal: {goal}\n\n"
    #                             "Inspect the CURRENT screenshot and determine whether the goal "
    #                             "has been completed.\n\n"
    #                             "Decision rules:\n"
    #                             "- If the requested application is open and the requested website "
    #                             "is visibly open, the goal is COMPLETE.\n"
    #                             "- If any required part of the goal is missing, the goal is NOT COMPLETE.\n"
    #                             "- Use only the current screenshot.\n"
    #                             "- Do not rely on previous actions or conversation text.\n\n"
    #                             "For this task, decide YES if the visible screen shows Chrome "
    #                             "open on YouTube.\n\n"
    #                             "Your FINAL answer must be exactly:\n"
    #                             "VERDICT=YES\n"
    #                             "or exactly:\n"
    #                             "VERDICT=NO"
    #                         )
    #                     },
    #                     {
    #                         "type":"image_url",
    #                         "image_url":{
    #                             "url":f"data:image/png;base64,{image_base64}",
    #                         }
    #                     }
    #                 ]
    #             }
    #         ]
    #     )
    #     print("\n--- Verifier Raw Response ---")
    #     print(response.content)
    #     content = str(response.content).strip().upper()

    #     # convert the model's response into a strict Yes/No verdict.
    #     if "VERDICT=YES" in verification.upper():
    #         return {"status": "completed", "results": results}

    #     if "VERDICT=UNKNOWN" in verification.upper():
    #         print("Verifier response was truncated/unparseable — retrying without counting as a failure.")
    #         continue  # or re-capture screenshot and loop again, don't touch failed_attempts


    def verify_task(self,goal,image,action_history):
        """Ask the vision whether the user's goal has been completed."""

        image_base64 = self.image_to_base64(image)

        response = self.llm.bind(max_tokens=200,reasoning_effort="none",).invoke(
            [
                {
                    "role":"user",
                    "content":[
                        {
                            "type":"text",
                            "text":(
                                f"User goal: {goal}\n\n"
                                f"Successful action history:\n{action_history}\n\n"
                                "Inspect the CURRENT screenshot and determine whether the goal "
                                "has been completed.\n\n"
                                "Decision rules:\n"
                                "- The goal is COMPLETE only when every required part of the goal "
                                "has been satisfied.\n"
                                "- Use the CURRENT screenshot to verify actions that should leave "
                                "visible evidence, such as opening an application or displaying text.\n"
                                "- Use the successful action history as evidence for actions that "
                                "may not leave permanent visible evidence, such as pressing a key, "
                                "moving the mouse, or clicking.\n"
                                "- An action in the history is evidence only when its verification "
                                "status shows that it executed successfully.\n"
                                "- Do not mark the task COMPLETE merely because the latest action "
                                "succeeded.\n"
                                "- If any required action or visible result is still missing, return "
                                "VERDICT=NO.\n"
                                "- Consider the entire user goal, not just the latest action.\n\n"
                                "Your FINAL answer must be exactly:\n"
                                "VERDICT=YES\n"
                                "or exactly:\n"
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
        print("\n--- Verifier Raw Response ---")
        print(response.content)
        content = str(response.content).strip().upper()

        # convert the model's response into a strict verdict.
        if "VERDICT=YES" in content:
            return "VERDICT=YES"

        if "VERDICT=NO" in content:
            return "VERDICT=NO"

        # Truncated or malformed output — this is a verifier failure, not a task failure.
        return "VERDICT=UNKNOWN"

    def run(self,goal,max_steps=5):
        """Run the computer use loop for a limited number of steps. """

        task_context = TaskContext(goal)

        results = task_context.results

        action_history = task_context.action_history

        # Start the task in the incomplete state.

        task_context.set_state(TaskState.TASK_INCOMPLETE)

        self.retry_manager.reset()

        # start every new task as incomplete.

        # Take the initial screenshot before deciding what to do.
        image = capture_screen()

        plan = self.planner.create_plan(goal)
        task_context.set_plan(plan)
        print("\n---Task Plan---")
        print(plan)

        for step in range(max_steps):
            print(f"\n--- Step {step + 1}---")

            # Ask the vision model to choose the next action.
            response = self.ask_vision_model(goal,image,action_history,plan)

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

                verification = self.verify_task(goal,image,action_history)

                print(f"Verification: {verification}")

                if "VERDICT=YES" in verification.upper():
                    task_context.set_state(TaskState.TASK_COMPLETE)
                    return {
                        "status":"completed",
                        "results":results,
                    }

                task_context.set_state(TaskState.TASK_INCOMPLETE)

                # Continue the agent loop with the current screenshot
                continue

                

            # Execute the tools selected by the model
            for tool_call in response.tool_calls:
                print(f"Selected tool: {tool_call['name']}")
                print(f"Arguments: {tool_call['args']}")
    
                result = execute_tool(tool_call)

                if isinstance(result, dict) and result.get("status") == "success":
                    self.retry_manager.reset()

                if isinstance(result,dict) and result.get("status") == "error":
                    retry_allowed = self.retry_manager.record_failure()

                    task_context.set_state(TaskState.ACTION_FAILED)

                    print(
                        f"Tool execution failed."
                        f"Retry allowed: {retry_allowed}"
                    )

                    if not retry_allowed:
                        return {
                            "status" : "failed",
                            "results" : results
                        }

                # stop this execution cycle if the user denied the action.
                if isinstance(result,dict) and result.get("status") == "denied":

                    # Mark the task as permission denied.
                    task_context.set_state(TaskState.PERMISSION_DENIED)

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
                task_context.add_action(
                    
                    tool_call["name"],
                    tool_call["args"],
                    "executed_successfully",
                    
                )

                # Give the application time to open or respond.
                time.sleep(2)

                # Observe the computer again after executing the action.
                image = capture_screen()

                # verify whether the user's goal has been completed.
                verification = self.verify_task(goal,image,action_history)

                print(f"Verification: {verification}")

                if "VERDICT=YES" in verification.upper():
                    return{
                        "status":"completed",
                        "results":results
                    }

                
        return {
            "status":"max_steps_reached",
            "results":results,
        }
