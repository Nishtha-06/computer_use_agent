# This file tests the connection between the Computer Use Agent
# and the Groq language model.

from computer.llm import create_llm

llm = create_llm()

response = llm.invoke(
    "Reply with exactly: Computer Use Agent LLM connected."
)

print(response.content)