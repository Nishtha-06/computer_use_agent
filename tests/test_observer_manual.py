# this file manually tests the computer use Agent;s screen observation
# functions by caputring the current screen and saving the screenshot.

from computer.observer import capture_screen,save_screenshot

#capture the current computer screen.
image = capture_screen()

#save the captured screen for inspection
file_path = save_screenshot(image)

print("Observation captured successfully.")
print(f"Screenshot saved to: {file_path}")
print(f"Screenshot size: {image.size}")