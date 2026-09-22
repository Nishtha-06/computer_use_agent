# This file creates a task planner for the Computer Use Agent.
# It converts a user's goal into a short plan while preferring
# direct computer tools over unnecessary mouse interactions.

from computer.llm import create_llm

class TaskPlanner:
    """Create a simple plan from the user's goal."""

    def __init__(self):
        self.llm = create_llm()

    @staticmethod
    def _interaction_violation(goal: str, plan: str) -> str | None:
        """Return a repair instruction when the plan changes the requested input method."""
        goal_text = goal.lower()
        plan_text = plan.lower()

        if "click" in goal_text:
            if "tool_click" not in plan_text:
                return (
                    "The goal explicitly requires a mouse click. "
                    "The plan must include tool_click."
                )

            if "tool_press_key" in plan_text:
                return (
                    "The goal explicitly requires a mouse click. "
                    "Do not replace the click with tool_press_key."
                )

        if "type" in goal_text:
            if "tool_type_text" not in plan_text:
                return (
                    "The goal explicitly requires typing text. "
                    "The plan must include tool_type_text."
                )

        if "press" in goal_text:
            if "tool_press_key" not in plan_text:
                return (
                    "The goal explicitly requires pressing a key. "
                    "The plan must include tool_press_key."
                )

        return None

    def create_plan(self,goal:str):
        """Generate a short step by step plan for the given goal."""

        prompt = f"""Create a simple step by step plan for this computer task:
            
            User goal:
            {goal}

Available computer tools:
- tool_screenshot
- tool_open_application
- tool_open_url
- tool_type_text
- tool_press_key
- tool_move_mouse
- tool_click

Planning rules:
1. Prefer direct tools whenever a direct tool can perform the action.
2. Use tool_open_application to open applications.
3. Use tool_open_url to open specific URLs.
4. Use tool_type_text to enter text.
5. Use tool_press_key for keyboard keys.
6. Use tool_move_mouse and tool_click only when necessary for
   UI interactions that cannot be performed by another direct tool.
7. Do not use the Windows Start menu to open an application when
   tool_open_application can open it directly.
8. Do not add unnecessary mouse clicks.
9. Keep the plan short and practical.
10. Do not provide code.
11. Do not execute anything.
12. Return only the numbered plan.
"""

        response = self.llm.invoke(prompt)
        plan = response.content
        violation = self._interaction_violation(goal, plan)

        if violation is not None:
            repair_prompt = f"""Regenerate the plan for this computer task.

User goal:
{goal}

Previous plan:
{plan}

Required correction:
{violation}

Return only a short numbered plan using the available tool names. Do not execute anything.
"""
            repaired_response = self.llm.invoke(repair_prompt)
            repaired_plan = repaired_response.content

            if self._interaction_violation(goal, repaired_plan) is None:
                plan = repaired_plan

        return plan