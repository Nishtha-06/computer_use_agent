# this module provides functions to control the computer 
# such as mouse movement, keyboard typing, opening applications and URLs, and taking screenshots.

import os
import ctypes
import webbrowser
# import subprocess


def set_dpi_awareness():
    """Make the Windows process DPI-aware before using screen coordinates."""
    if os.name != "nt":
        return

    try:
        # Per Monitor V2 DPI awareness.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except (AttributeError, OSError):
        # Fallback for older Windows environments.
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


set_dpi_awareness()

import pyautogui

# Store the dimensions of the latest screenshot.
LAST_SCREENSHOT_SIZE = None


def screenshot():
    """Capture and return the current computer screen."""
    global LAST_SCREENSHOT_SIZE

    image = pyautogui.screenshot()
    LAST_SCREENSHOT_SIZE = image.size

    return image

def move_mouse(x:int,y:int):
    """Move the mouse cursor to the given screen coordinates."""

    pyautogui.moveTo(x,y,duration=0.2)

def convert_screenshot_point_to_screen(x, y):
    """Convert screenshot coordinates into physical screen coordinates."""
    x, y = validate_screenshot_point(x, y)
    screen_width, screen_height = pyautogui.size()

    if LAST_SCREENSHOT_SIZE is None:
        return x, y

    image_width, image_height = LAST_SCREENSHOT_SIZE

    if image_width <= 0 or image_height <= 0:
        return x, y

    scale_x = screen_width / image_width
    scale_y = screen_height / image_height

    screen_x = round(x * scale_x)
    screen_y = round(y * scale_y)

    return screen_x, screen_y


def validate_screenshot_point(x, y, image_size=None):
    """Validate a point in screenshot coordinates before conversion."""
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Screenshot coordinates must be numeric.")

    width, height = image_size or LAST_SCREENSHOT_SIZE or pyautogui.size()
    if width <= 0 or height <= 0 or not (0 <= x < width and 0 <= y < height):
        raise ValueError(
            f"Screenshot coordinate ({x}, {y}) is outside {width}x{height}."
        )

    return round(x), round(y)


def click_point_from_bounding_box(bounding_box, image_size=None):
    """Return the center of a valid [x1, y1, x2, y2] screenshot box."""
    if not isinstance(bounding_box, (list, tuple)) or len(bounding_box) != 4:
        raise ValueError("Bounding box must contain four coordinates.")

    x1, y1, x2, y2 = bounding_box
    if any(not isinstance(value, (int, float)) for value in bounding_box):
        raise ValueError("Bounding-box coordinates must be numeric.")

    width, height = image_size or LAST_SCREENSHOT_SIZE or pyautogui.size()
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError(
            f"Bounding box {bounding_box} is outside {width}x{height} or has zero size."
        )

    return validate_screenshot_point((x1 + x2) / 2, (y1 + y2) / 2, (width, height))


def click(x=None, y=None, bounding_box=None):
    """Click using screenshot coordinates converted to screen coordinates."""
    if bounding_box is not None:
        x, y = click_point_from_bounding_box(bounding_box)

    if x is not None and y is not None:
        screen_x, screen_y = convert_screenshot_point_to_screen(x, y)

        print(
            f"Click coordinate conversion: "
            f"screenshot=({x}, {y}) → screen=({screen_x}, {screen_y})"
        )

        pyautogui.click(screen_x, screen_y)
    else:
        pyautogui.click()

def type_text(text):
    """Typer the give text using keyboard."""
    pyautogui.write(text,interval=0.03)

def press_key(key):
    """Type a keyboard key such as Enter,ESC or ctrl."""
    pyautogui.press(key)

def open_application(application):
    """Open a Windows application using its executable name."""
    os.startfile(application)

def open_url(url):
    """Open a ULR in the defualt web browser."""
    webbrowser.open(url)

if __name__ == "__main__":
    print("Computer controller loaded successfully.")