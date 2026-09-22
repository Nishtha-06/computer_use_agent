# computer/element_locator.py
"""
Semantic element grounding via Windows UI Automation (pywinauto).

Given a semantic target (e.g. "5", "Calculator") and an optional
app_hint (window title substring), returns a bounding box / center
the existing controller can click — without any vision model pixel
grounding involved.

This module does NOT touch agent.py, controller.py, executor.py,
observer.py, verifier.py, retry.py, task_context.py, or audit.py.
It only produces the same bounding_box/center shape those already
consume.
"""

# Add near the top of element_locator.py

_DIGIT_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
}

_OPERATOR_ALIASES = {
    "+": "plus", "-": "minus", "*": "multiply by", "x": "multiply by",
    "/": "divide by", "=": "equals", ".": "decimal separator",
}

def _candidate_names(target: str) -> list[str]:
    """Given a raw semantic target, generate the variant strings worth
    matching against automation_id / name — handles the case where a
    digit or symbol target ('5', '+') needs to match a spelled-out
    UIA name ('Five', 'Plus') or a conventional auto_id pattern
    ('num5Button')."""
    t = target.strip()
    t_lower = t.lower()
    variants = {t_lower}

    if t_lower in _DIGIT_WORDS:
        variants.add(_DIGIT_WORDS[t_lower])          # "5" -> "five"
        variants.add(f"num{t_lower}button")           # "5" -> "num5button"
    if t_lower in _OPERATOR_ALIASES:
        variants.add(_OPERATOR_ALIASES[t_lower])       # "+" -> "plus"

    return list(variants)

from dataclasses import dataclass
from typing import Optional
import time
from pywinauto import Desktop
import re

@dataclass
class LocateResult:
    found: bool
    target: str
    bounding_box: Optional[list] = None   # [x1, y1, x2, y2]
    center: Optional[list] = None         # [x, y]
    method: str = "uia"
    app_hint: Optional[str] = None
    matched_by: Optional[str] = None      # "automation_id" | "name"
    error: Optional[str] = None


def _get_window(app_hint: str, timeout: float = 5.0):
    """Poll the Desktop for a window whose title contains app_hint.
    Uses find_elements (plural) instead of Desktop(...).window(...)
    because some apps — confirmed for Calculator, likely other
    ApplicationFrameHost-hosted UWP apps — register multiple UIA
    top-level elements for what is visually a single window (same
    pid, same rectangle, same control tree, different handle/runtime_id).
    Desktop(...).window(...) raises ElementAmbiguousError in that case;
    find_elements does not, so we just take the first match, which is
    safe here since all matches are functionally identical."""
    from pywinauto.findwindows import find_elements
    from pywinauto.controls.uiawrapper import UIAWrapper

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            elements = find_elements(
                title_re=f"(?i).*{re.escape(app_hint)}.*",
                backend="uia",
                top_level_only=True,
                visible_only=True,
            )
            if elements:
                return UIAWrapper(elements[0])
        except Exception:
            pass
        time.sleep(0.3)
    return None


def find_element(
    target: str,
    app_hint: Optional[str] = None,
    control_type: Optional[str] = None,
    timeout: float = 5.0,
) -> LocateResult:
    """
    target: semantic name to match, e.g. "5", "Submit"
             (matched against automation_id first, then name)
    app_hint: window title substring, e.g. "Calculator"
    control_type: optional UIA control type filter, e.g. "Button"
                   (narrows the search and avoids the auto_id
                   kwarg issue in descendants())
    """
    if not app_hint:
        return LocateResult(found=False, target=target, method="uia",
                             error="app_hint is required for this version "
                                   "of find_element")

    window = _get_window(app_hint, timeout=timeout)
    if window is None:
        return LocateResult(found=False, target=target, method="uia",
                             app_hint=app_hint,
                             error=f"no window matching '{app_hint}' found "
                                   f"within {timeout}s")

    try:
        # NOTE: descendants() on this pywinauto version does not accept
        # automation_id/auto_id as a filter kwarg (raises TypeError on
        # IUIA.build_condition()). Filter by control_type only, then
        # match automation_id / name in Python. Confirmed working
        # against Calculator's "5" button.
        candidates = window.descendants(control_type=control_type) if control_type \
            else window.descendants()
    except Exception as e:
        return LocateResult(found=False, target=target, method="uia",
                             app_hint=app_hint, error=f"descendants() failed: {e}")

    match = None
    matched_by = None
    target_lower = target.lower()

    candidate_names = _candidate_names(target)

    # Pass 1: exact automation_id match
    for el in candidates:
        auto_id = (el.element_info.automation_id or "").lower()
        if auto_id and any(auto_id == v or auto_id.startswith(v) for v in candidate_names):
            match = el
            matched_by = "automation_id"
            break

    # Pass 2: name match
    if not match:
        for el in candidates:
            name = (el.window_text() or "").lower()
            if name and any(name == v for v in candidate_names):
                match = el
                matched_by = "name"
                break

    if not match:
        return LocateResult(found=False, target=target, method="uia",
                             app_hint=app_hint,
                             error="no element matched target by "
                                   "automation_id or name")

    rect = match.rectangle()
    bbox = [rect.left, rect.top, rect.right, rect.bottom]
    center = [(rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2]

    return LocateResult(found=True, target=target, bounding_box=bbox,
                         center=center, method="uia", app_hint=app_hint,
                         matched_by=matched_by)