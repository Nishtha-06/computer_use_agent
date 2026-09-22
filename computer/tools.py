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
def tool_click(
    x: list[int] | None = None,
    target: str | None = None,
    bounding_box: list[int] | None = None,
):
    """Click at screen coordinates [x, y].
    Use this only when a direct computer tool cannot perform the required action."""
    if bounding_box is not None:
        click(bounding_box=bounding_box)
    elif x is not None and len(x) == 2:
        click(x[0], x[1])
    else:
        raise ValueError("tool_click requires x=[x, y] or bounding_box=[x1, y1, x2, y2].")

@tool
def tool_type_text(text:str):
    """Type the provided text using the keyboard."""
    type_text(text)

@tool
def tool_press_key(key:str):
    """Press a keyboard key such as Enter, Escape, or Tab."""
    press_key(key)

@tool
def tool_open_application(application: str):
    """Open a Windows application using its executable name.
    The application argument must be a string containing the executable name.
    Examples:
    - "notepad" for Notepad
    - "chrome" for Google Chrome
    - "calc" for Calculator

    Do not use display names such as "Google Chrome".
    Do not click the application's taskbar or desktop icon instead."""
    open_application(application)

@tool
def tool_open_url(url:str):
    """Open a URL directly in the default web browser.
    Prefer this tool whenever the user provides a specific URL."""
    open_url(url)
