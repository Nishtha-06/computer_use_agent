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
        self.failed_click_points = []
        self.semantic_failure_count = 0

    def set_plan(self,plan: str):
        """Store the generated task plan."""
        self.plan = plan

    def add_action(self,tool_name,arguments,verification = "unknown",result=None):
        """Store an action performed by the agent."""
        action = {
            "tool":tool_name,
            "arguments":arguments,
            "verification":verification
        }
        if result is not None:
            action["result"] = result
        self.action_history.append(action)
    def add_failed_click_point(self, x, y):
        """Store a click coordinate that failed goal verification."""
        self.failed_click_points.append((x, y))

    def is_near_failed_click(self, x, y, threshold=25):
        """Check whether a click is close to a previously failed click."""
        for failed_x, failed_y in self.failed_click_points:
            distance_squared = (
                (x - failed_x) ** 2
                + (y - failed_y) ** 2
            )

            if distance_squared <= threshold ** 2:
                return True

        return False

    def record_semantic_failure(self, x=None, y=None):
        """Record goal failure separately from a tool execution error."""
        self.semantic_failure_count += 1
        if x is not None and y is not None:
            self.add_failed_click_point(x, y)

    def has_exceeded_semantic_failures(self, limit=3):
        """Return whether semantic recovery has reached its bounded limit."""
        return self.semantic_failure_count >= limit

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
            "state":self.state,
            "failed_click_points":self.failed_click_points,
            "semantic_failure_count":self.semantic_failure_count,
        }