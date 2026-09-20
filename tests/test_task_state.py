# This file manually tests the TaskState component
# of the Computer Use Agent.

from computer.task_state import TaskState

task_state = TaskState()

print("\n---Task State Test---")

print("Initial state:",task_state.get_state())

task_state.set_state(TaskState.TASK_INCOMPLETE)
print("\nAfter incomplete:")
print("State:", task_state.get_state())

task_state.set_state(TaskState.ACTION_FAILED)
print("\nAfter action failure:")
print("State:", task_state.get_state())
print("Is failed:", task_state.is_failed())

task_state.set_state(TaskState.PERMISSION_DENIED)
print("After permission denial:", task_state.get_state())

task_state.set_state(TaskState.TASK_COMPLETE)
print("\nAfter completion:")
print("State:", task_state.get_state())
print("Is complete:", task_state.is_complete())