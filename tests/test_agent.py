# This file tests the basic Computer Use Agent by giving it a goal
# and checking whether it selects and executes the appropriate tool.

from computer.agent import ComputerUseAgent

#create the computer use agent
agent = ComputerUseAgent()

#Give the agent a computer task.
result = agent.run("Open Notepad and type 'Hello, This is Computer Use Agent'.",max_steps=5)

#Display result
print("\n Final Agent result: ")
print(result)
