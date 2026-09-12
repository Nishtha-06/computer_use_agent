# this file provides screen observation functions for the computer use agent.
#it captures the current screen and saves observations for later analysis.

from datetime import datetime
from pathlib import Path

from computer.controller import screenshot

#directory where captured screenshots will be stored.
SCREENSHOT_DIR = Path("screenshots")

def capture_screen():
    """Capture and return the current computer screen."""
    return screenshot()

def save_screenshot(image):
    """Save a captured screenshot with a timestamped filename."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = SCREENSHOT_DIR / f"screen_{timestamp}.png"

    image.save(file_path)

    return file_path