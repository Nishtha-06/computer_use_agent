# this file provides screen observation functions for the computer use agent.
#it captures the current screen and saves observations for later analysis.

from datetime import datetime
from pathlib import Path

from PIL import ImageDraw

from computer.controller import screenshot

#directory where captured screenshots will be stored.
SCREENSHOT_DIR = Path("screenshots")
CLICK_DEBUG_DIR = Path("logs") / "click_debug"

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

def save_click_debug(image, x, y, target=None, bounding_box=None, step=None):
    """Save click evidence with target, box, and step metadata when available."""
    CLICK_DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    debug_image = image.copy()
    draw = ImageDraw.Draw(debug_image)

    if bounding_box and len(bounding_box) == 4:
        draw.rectangle(tuple(bounding_box), outline="yellow", width=3)

    if target:
        draw.text((x + 16, y + 16), f"target: {target}", fill="yellow")

    radius = 12

    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius,
        ),
        outline="red",
        width=4,
    )

    draw.line(
        (x - 20, y, x + 20, y),
        fill="red",
        width=3,
    )

    draw.line(
        (x, y - 20, x, y + 20),
        fill="red",
        width=3,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_path = CLICK_DEBUG_DIR / f"click_{timestamp}.png"

    debug_image.save(file_path)

    return file_path