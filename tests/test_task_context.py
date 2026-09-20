# This file manually tests the TaskContext component
# of the Computer Use Agent

from computer.task_context import TaskContext
from computer.task_state import TaskState

context = TaskContext(
    "Open Notepad and type Hello from Computer Use Agent"
)

context.set_plan(
    "1. Open Notepad.\n"
    "2. Type the requested text."
)

context.add_action(
    "tool_open_application",
    {"application": "notepad"},
    "incomplete",
)

context.add_result(None)

print("\n--- Task Context Test ---")
print(context.get_context())

context.set_state(TaskState.TASK_COMPLETE)

print("\nAfter completion:")
print(context.get_context())

context.set_state(TaskState.ACTION_FAILED)

print("\nAfter action failure:")
print(context.get_context())