# This file defines the possoble states of a Computer Use Agent task.
# It helps the agent distinguish between an incomplete task,
# a completed task, and an actual failure.

class TaskState:
    """Represent the current state of a computer task."""

    TASK_INCOMPLETE = "task_incomplete"
    TASK_COMPLETE = "task_complete"
    ACTION_FAILED = "action_failed"
    PERMISSION_DENIED = "permission_denied"

    def __init__(self):
        """Start with an incomplete task state."""
        self.current_state = self.TASK_INCOMPLETE

    def set_state(self,state: str):
        """Update the current task state."""
        self.current_state = state

    def get_state(self):
        """Return the current task state."""
        return self.current_state

    def is_complete(self):
        """Return True when the task is complete."""
        return self.current_state == self.TASK_COMPLETE

    def is_failed(self):
        """Return True when an action has actually failed."""
        return self.current_state == self.ACTION_FAILED
    