# this file contains the basic computer use agent that connects the
# user's goal, the groq LLM,computer tools and tool execution.

import base64
from io import BytesIO

import time

from computer.element_locator import find_element

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
from computer.controller import click_point_from_bounding_box, validate_screenshot_point
from computer.observer import (
    capture_screen,
    save_screenshot,
    save_click_debug,
)
from computer.retry import RetryManager

def _derive_app_hint(application: str) -> str:
    """Best-effort conversion of a launch string (e.g. 'calc.exe') into a
    substring likely to appear in that app's real window title (e.g.
    'calc', which matches 'Calculator' via the substring match in
    element_locator._get_window). This is a heuristic, not exact —
    it happened to work for calc.exe -> 'Calculator' because 'calc' is
    a literal substring. It is NOT guaranteed to work for apps whose
    process name doesn't resemble their window title (e.g. chrome.exe
    vs 'Google Chrome' — case and wording both differ). Revisit this
    once more than one app is tested.
    """
    name = application.strip()
    for ext in (".exe", ".app", ".lnk"):
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
            break
    return name

class ComputerUseAgent:
    """Computer Use Agent that observes the screen and executes actions."""

    SEMANTIC_FAILURE_LIMIT = 3
    REJECTED_CLICK_LIMIT = 3

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
            blocked_clicks = []
            for item in action_history:
                history_text += (
                    f"{item['tool']}({item['arguments']})\n"
                    f"[execution status: {item.get('verification','unknown')}]\n"
                    f"[goal verification: {item.get('verification_result','unknown')}]\n"
                    f"[result: {item.get('result','unknown')}]\n"
                    )
                if item.get("tool") != "tool_click":
                    continue

                arguments = item.get("arguments") or {}
                click_point = arguments.get("x")
                if (
                    not isinstance(click_point, (list, tuple))
                    or len(click_point) != 2
                ):
                    continue

                result = item.get("result") or {}
                should_block = (
                    item.get("verification_result") == "VERDICT=NO"
                    or item.get("verification") == "execution_rejected"
                    or result.get("status") == "rejected"
                )
                if should_block:
                    normalized_point = [click_point[0], click_point[1]]
                    if normalized_point not in blocked_clicks:
                        blocked_clicks.append(normalized_point)

            blocked_clicks_text = (
                str(blocked_clicks)
                if blocked_clicks
                else "None"
            )

        else:
            history_text = "No actions have been performed yet."
            blocked_clicks_text = "None"

        response = self.llm_with_tools.bind(reasoning_effort="none").invoke(
            [
                {
                    "role":"user",
                    "content":[
                        {
                            "type":"text",
                            "text":(
                                f"User goal: {goal}\n\n"
                                f"Current screenshot dimensions: {image.width} x {image.height} pixels.\n"
                                f"All mouse coordinates must be within "
                                f"x=0..{image.width - 1}, y=0..{image.height - 1}.\n\n"
                                f"Task plan:\n{plan}\n\n"
                                f"Actions already performed:\n{history_text}\n\n"
                                f"PROHIBITED CLICK COORDINATES: {blocked_clicks_text}\n\n"

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

                                "12. If the previous verification result was VERDICT=NO, "
                                "treat the previous action as unsuccessful for the user's goal.\n"

                                "13. After VERDICT=NO, do NOT repeat the exact same action "
                                "with the same arguments.\n"

                                "14. After VERDICT=NO, inspect the current screenshot again "
                                "and choose a different action or different coordinates.\n"

                                "15. For UI click tasks, successful execution of tool_click only "
                                "means the mouse click occurred; it does NOT prove that the "
                                "intended UI element was clicked.\n"

                                "16. If a click did not achieve the goal, choose a new location "
                                "based on the current screenshot instead of repeating the previous coordinates.\n"

                                "17. Use the current screenshot together with the action history "
                                "to decide the next action.\n"

                                "18. Do not click the taskbar to interact with an application "
                                "that is already open.\n"

                                "19. After opening an application, inspect the screenshot before "
                                "deciding whether another action is necessary.\n"

                                "20. If the required application is already visible and usable, "
                                "interact with it directly rather than reopening or selecting it "
                                "from the taskbar.\n"

                                "21. A status of 'executed_goal_incomplete' means that action "
                                "succeeded — do not repeat it. Build on the resulting screen state instead.\n"

                                "22. If the application required by the goal is already visible "
                                "and open in the current screenshot, do NOT call "
                                "tool_open_application again. Interact with what's already on "
                                "screen (click, type, or navigate) instead.\n"

                                "23. The current screenshot is already provided to you. Do not "
                                "call tool_screenshot just to inspect the current screen again.\n"

                                "24. If the previous action was tool_open_application and it "
                                "succeeded, and the task requires entering text into that "
                                "application, select tool_type_text with the exact text required "
                                "by the user's goal.\n"

                                "25. When selecting tool_type_text, never use null or None for "
                                "the text argument. Extract the exact text that the user wants "
                                "typed from the goal or task plan.\n"

                                "26. For visual clicks, identify the target by name and provide "
                                "bounding_box=[x1,y1,x2,y2] in screenshot coordinates. The box "
                                "must tightly surround the complete visible target, be inside "
                                "the screenshot, and have non-zero size. Do not guess a click "
                                "point when a bounding box can be identified. Do not calculate "
                                "the center; the controller will calculate it.\n"

                                "27. execution_rejected means the action was not executed and "
                                "must not be treated as progress toward completion. Read its "
                                "result reason before selecting the next action.\n"

                                "28. Never select a click coordinate listed in PROHIBITED "
                                "CLICK COORDINATES.\n"

                                "29. If the previous click received VERDICT=NO, use the CURRENT "
                                "screenshot to find the target again and choose a different "
                                "coordinate.\n"

                                "30. If a click was rejected because that region already failed, "
                                "do not request the same coordinate again.\n"

                                "31. The PROHIBITED CLICK COORDINATES list is an enforced "
                                "constraint, not a suggestion. Do not select any listed point "
                                "or a nearby point; choose a new target location from the "
                                "current screenshot.\n"
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
                                f"Action history:\n{action_history}\n\n"
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
                                "- An action is evidence of completion only when its verification "
                                "status shows that it executed successfully.\n"
                                "- Failed actions must NOT be treated as evidence that the goal "
                                "was completed.\n"
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
        # Tracks the application the agent believes is currently active,
        # used as app_hint for UIA grounding. Set after a successful
        # tool_open_application call. This is agent-level execution
        # context, not part of the planner's output (see design decision:
        # app_hint comes from agent context, not planner schema).
        active_app_hint = None

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
            action_failed = False

            for tool_call in response.tool_calls:
                print(f"Selected tool: {tool_call['name']}")
                print(f"Arguments: {tool_call['args']}")

                if tool_call["name"] == "tool_click":
                    click_arguments = dict(tool_call["args"])
                    bounding_box = click_arguments.get("bounding_box")

                if tool_call["name"] == "tool_click":
                    click_arguments = dict(tool_call["args"])
                    bounding_box = click_arguments.get("bounding_box")

                    # --- UIA grounding layer ---
                    # Try exact semantic grounding before falling back to
                    # the vision model's own bounding_box guess (already
                    # present in click_arguments from this same Qwen call).
                    # A UIA miss is NOT a semantic failure — it only means
                    # this grounding method couldn't find the element, not
                    # that anything was clicked incorrectly. It is not
                    # recorded via retry_manager or record_semantic_failure.
                   
                    # target = click_arguments.get("target")
                    # if target:
                    #     uia_result = find_element(target=target, app_hint=active_app_hint)
                    target = click_arguments.get("target")
                    if target and active_app_hint:
                        uia_result = find_element(target=target, app_hint=active_app_hint)
                        if uia_result.found:
                            bounding_box = uia_result.bounding_box
                            click_arguments["bounding_box"] = bounding_box
                            print(
                                f"[UIA] grounded target={target!r} "
                                f"app_hint={active_app_hint!r} via "
                                f"{uia_result.matched_by} -> {bounding_box}"
                            )
                        else:
                            print(
                                f"[UIA] miss for target={target!r} "
                                f"app_hint={active_app_hint!r}: "
                                f"{uia_result.error}; using vision-model "
                                f"bounding_box instead"
                            )
                    # --- end UIA grounding layer ---

                    

                    try:
                        if bounding_box is not None:
                            click_x, click_y = click_point_from_bounding_box(
                                bounding_box,
                                image.size,
                            )
                            click_arguments["x"] = [click_x, click_y]
                        else:
                            click_args = click_arguments.get("x")
                            if not isinstance(click_args, (list, tuple)) or len(click_args) != 2:
                                raise ValueError("tool_click requires x=[x, y] or a valid bounding_box.")
                            click_x, click_y = validate_screenshot_point(
                                click_args[0], click_args[1], image.size
                            )
                            click_arguments["x"] = [click_x, click_y]
                    except ValueError as error:
                        result = {
                            "status": "rejected",
                            "tool": "tool_click",
                            "reason": str(error),
                        }
                        results.append({
                            "step": step + 1,
                            "tool": "tool_click",
                            "arguments": click_arguments,
                            "result": result,
                        })
                        task_context.add_action(
                            "tool_click", click_arguments, "execution_rejected", result
                        )
                        continue

                    if task_context.is_near_failed_click(click_x, click_y):
                        result = {
                            "status": "rejected",
                            "tool": "tool_click",
                            "reason": (
                                "That region already failed. Re-examine the current "
                                "screenshot and choose a different coordinate."
                            ),
                        }
                        results.append({
                            "step": step + 1,
                            "tool": "tool_click",
                            "arguments": click_arguments,
                            "result": result,
                        })
                        task_context.add_action(
                            "tool_click", click_arguments, "execution_rejected", result
                        )
                        rejected_clicks = sum(
                            1
                            for action in task_context.action_history
                            if (
                                action.get("tool") == "tool_click"
                                and action.get("verification") == "execution_rejected"
                            )
                        )
                        if rejected_clicks >= self.REJECTED_CLICK_LIMIT:
                            task_context.set_state(TaskState.ACTION_FAILED)
                            return {
                                "status": "failed",
                                "reason": (
                                    "The action-selection model repeatedly selected a "
                                    "previously rejected click region."
                                ),
                                "results": results,
                            }
                        continue

                    debug_path = save_click_debug(
                        image,
                        click_x,
                        click_y,
                        click_arguments.get("target"),
                        bounding_box,
                        step + 1,
                    )
                    print(f"Click debug screenshot: {debug_path}")
                    tool_call = dict(tool_call)
                    tool_call["args"] = click_arguments

                result = execute_tool(tool_call)

                if isinstance(result, dict) and result.get("status") == "success":
                    self.retry_manager.reset()

                if isinstance(result, dict) and result.get("status") == "success":
                    self.retry_manager.reset()

                # Update active-app context for UIA grounding. Deliberately
                # not counted as a semantic failure or retry event — this
                # is just bookkeeping for later find_element() calls.
                if (
                    tool_call["name"] == "tool_open_application"
                    and isinstance(result, dict)
                    and result.get("status") == "success"
                ):
                    application = tool_call["args"].get("application", "")
                    active_app_hint = _derive_app_hint(application)
                    print(f"[context] active_app_hint set to {active_app_hint!r}")

                if isinstance(result,dict) and result.get("status") == "error":
                    retry_allowed = self.retry_manager.record_failure()

                    task_context.set_state(TaskState.ACTION_FAILED)

                    results.append(
                        {
                            "step":step+1,
                            "tool":tool_call["name"],
                            "arguments":tool_call["args"],
                            "result":result
                        }
                    )

                    print(
                        f"Tool execution failed."
                        f"Retry allowed: {retry_allowed}"
                    )

                    if not retry_allowed:
                        return {
                            "status" : "failed",
                            "results" : results
                        }
                    action_failed = True
                    break

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

                verification_status = (
                    "executed_successfully"
                    if isinstance(result,dict) and result.get("status") == "success"
                    else "execution_failed"
                )

                # Record the action for the next LLM decision.
                task_context.add_action(

                    tool_call["name"],
                    tool_call["args"],
                    verification_status,
                    result,
                    
                )

                # Give the application time to open or respond.
                time.sleep(2)

                # Observe the computer again after executing the action.
                image = capture_screen()

                # verify whether the user's goal has been completed.
                verification = self.verify_task(goal,image,action_history)

                print(f"Verification: {verification}")
                if task_context.action_history:
                    task_context.action_history[-1]["verification_result"] = verification

                if "VERDICT=YES" in verification.upper():
                    return{
                        "status":"completed",
                        "results":results
                    }

                if (
                    tool_call["name"] == "tool_click"
                    and verification == "VERDICT=NO"
                    and isinstance(result, dict)
                    and result.get("status") == "success"
                ):
                    task_context.record_semantic_failure(click_x, click_y)
                    task_context.action_history[-1]["verification"] = "executed_successfully"
                    task_context.action_history[-1]["verification_result"] = verification
                    if task_context.has_exceeded_semantic_failures(
                        self.SEMANTIC_FAILURE_LIMIT
                    ):
                        task_context.set_state(TaskState.ACTION_FAILED)
                        return {
                            "status": "failed",
                            "reason": (
                                "The click executed, but repeated screenshot verification "
                                "did not confirm the requested UI target."
                            ),
                            "results": results,
                        }

                if action_failed:
                    continue

                
        return {
            "status":"max_steps_reached",
            "results":results,
        }
if __name__ == "__main__":
    agent = ComputerUseAgent()
    goal = input("Enter your computer task: ")
    result = agent.run(goal)
    print("\n--- Final Result ---")
    print(result)
