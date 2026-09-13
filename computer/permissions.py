# This file provides the permission-checking layer for the
# Computer Use Agent before computer actions are executed.

# tools that can execute without permission
LOW_RISK_TOOLS = {
    "tool_screenshot",
    "tool_move_mouse",
    "tool_click",
    "tool_press_key",
    "tool_type_text",
}

# tools that require explicit user approval.
HIGH_RISK_TOOLS = {
    "tool_open_application",
    "tool_open_url",
}

def requires_permission(tool_name: str) -> bool:
    """Return True when a tool requires user permission."""

    if tool_name in HIGH_RISK_TOOLS:
        return True
    return False