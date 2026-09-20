# This file stores the important context of the current computer task.
# It keeps the user's goal,generated plan, executed actions and
# current task state together in one place.

from computer.task_state import TaskState

class TaskContext:
    """Store information about the current computer task."""

    def __init__(self,goal:str):
        """Initialize the context for a new task."""
        self.goal = goal
        self.plan = ""
        self.action_history = []
        self.results = []
        self.state = TaskState.TASK_INCOMPLETE

    def set_plan(self,plan: str):
        """Store the generated task plan."""
        self.plan = plan

    def add_action(self,tool_name,arguments,verification = "unknown"):
        """Store an action performed by the agent."""
        self.action_history.append (
            {
                "tool":tool_name,
                "arguments":arguments,
                "verification":verification
            }
        )

    def add_result(self,result):
        """Store the result returned by a tool."""
        self.results.append(result)

    def set_state(self,state:str):
        """Update the current task state"""
        self.state = state
    
    def get_context(self):
        """Return the complete current task context."""
        return {
            "goal":self.goal,
            "plan":self.plan,
            "action_history":self.action_history,
            "results":self.results,
            "state":self.state
        }