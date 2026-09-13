# this file tests the reusable screen analysis functionality of
# the computer use agent.

from computer.observer import capture_screen
from computer.vision import analyze_screen

# capture the current computer screen
image = capture_screen()

#send the screenshot to the vision model.
description = analyze_screen(image)

print("Screen analysis:")
print(description)