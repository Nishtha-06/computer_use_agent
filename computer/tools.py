# this file defines the tools that will later be available to the
# computer use agent. Each tool wraps a computer control function 
# and provides a clear interface for the future LLM agent.

from langchain_core.tools import tool

from computer.controller import click,move_mouse,open_application,open_url,press_key,screenshot,type_text

@tool
def tool_screenshot():
    """capture the current computer screen."""
    return screenshot()

@tool
def tool_move_mouse(x:list[int]):
    """Move the mouse cursor to the specified screen coordinates."""
    move_mouse(x[0],x[1])

@tool
def tool_click(x:list[int]):
    """Click at the specified screen coordinates."""
    click(x[0],x[1])

@tool
def tool_type_text(text):
    """Type the provided text using the keyboard."""
    type_text(text)

@tool
def tool_press_key(key):
    """Press a keyboard key such as Enter, Escape, or Tab."""
    press_key(key)

@tool
def tool_open_application(application):
    """Open a windows using its executable name."""
    open_application(application)

@tool
def tool_open_url(url):
    """Open a URL in the default web browser."""
    open_url(url)
