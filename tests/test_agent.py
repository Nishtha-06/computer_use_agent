# This file tests the basic Computer Use Agent by giving it a goal
# and checking whether it selects and executes the appropriate tool.

from computer.agent import ComputerUseAgent

#create the computer use agent
agent = ComputerUseAgent()

#Give the agent a computer task.
result = agent.run("Open Notepad on my computer.")

#Display result
print("Agent result: ")
print(result)

print("Observation: ")
print(f"Screenshot: {result.get('screenshot')}")