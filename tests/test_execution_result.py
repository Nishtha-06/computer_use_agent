# This file manually tests the structured execution-result
# helpers used by the Computer Use Agent.

from computer.execution_result import (
    success_result,
    denied_result,
    is_success,
    is_denied
)

success = success_result(
    "tool_type_text",
    None
)

denied = denied_result (
    "tool_open_application"
)

print("\n--- Execution Result Test ---")
print("Success result: ")
print(success)
print("Is success:", is_success(success))

print("\nDenied result:")
print(denied)
print("Is denied:", is_denied(denied))

