# This file tests the perimssion ruled used by the computer Use Agent.

from computer.permissions import requires_permission

print("Permission tests:")

print("tool click: ",requires_permission("tool_click"))

print(
    "tool_open_application:",
    requires_permission("tool_open_application")
)

print(
    "tool_open_url:",
    requires_permission("tool_open_url")
)