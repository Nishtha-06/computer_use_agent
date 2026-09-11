# Purpose:
# This file manually tests the Computer Use Agent's basic computer-control
# functions by opening Notepad, typing text, pressing a key, and capturing
# a screenshot.

import time

from computer.controller import(
    screenshot,
    open_application,
    type_text,
    press_key,
)

# open windows notepad.
open_application("notepad.exe")

#give notepad time to open
time.sleep(2)

#type a safe test message.
type_text("Hello from computer use agent!")

#press enter.
press_key("enter")

#capture the current screen.
image = screenshot()

print("Screenshot captured successfully.")
print(f"Screenshot size:{image.size}")
