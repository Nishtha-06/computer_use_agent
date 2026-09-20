# This file manually tests the task planner component
# of the Computer use Agent

from computer.planner import TaskPlanner

planner = TaskPlanner()

goal = "Open Notepad and type Hello from Computer Use Agent"

plan = planner.create_plan(goal)

print("\n--- Generated Plan ---")
print(plan)