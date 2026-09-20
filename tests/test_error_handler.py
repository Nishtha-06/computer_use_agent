# This file manually tests the error handling component
# of the Computer Use Agent

from computer.error_handler import handle_tool_error,is_error

try:
    raise RuntimeError("Test error")

except Exception as error:
    result = handle_tool_error(
        "tool_open_application",
        error,
    )

print("\n--- Error Handler Test ---")
print(result)
print("Is error:", is_error(result))