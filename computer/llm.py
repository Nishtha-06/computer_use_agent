# this file creates the groq language model used by the computer Use agent.
# the model will later be connected to computer-control tools.

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def create_llm():
    """Create and return the groq chat model."""
    return ChatGroq(
        model = "openai/gpt-oss-120b",
        temperature=0
    )