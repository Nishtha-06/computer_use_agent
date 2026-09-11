# this module provides functions to control the computer 
# such as mouse movement, keyboard typing, opening applications and URLs, and taking screenshots.

import time 
import webbrowser
import subprocess
from pathlib import Path

import pyautogui

def screenshot():
    """Capture and return the current computer screen."""
    return pyautogui.screenshot()

def move_mouse(x,y):
    """Move the mouse cursor to the given screen coordinates."""

    pyautogui.moveTo(x,y,duration=0.2)

def click(x=None,y=None):
    """Click at the given or click at the current position."""
    if x is not None and y is not None:
        pyautogui.click(x,y)
    else:
        pyautogui.click()

def type_text(text):
    """Typer the give text using keyboard."""
    pyautogui.write(text,interval=0.03)

def press_key(key):
    """Type a keyboard key such as Enter,ESC or ctrl."""
    pyautogui.press(key)

def open_application(application):
    """Open a windows application using its excutable or path."""
    subprocess.Popen(application)

def open_url(url):
    """Open a ULR in the defualt web browser."""
    webbrowser.open(url)

if __name__ == "__main__":
    print("Computer controller loaded successfully.")