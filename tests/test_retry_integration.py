# This file tests the connection between execution errors
# and the RetryManager used by the Computer Use Agent.

from computer.retry import RetryManager
from computer.error_handler import handle_tool_error

retry_manager = RetryManager(max_retries=3)

print("--- Retry Integration Test ---")

# Simulate a tool executiion error.
error_result = handle_tool_error(
    "tool_open_application",
    Exception("Application could not be opned.")
)

print("Error result:")
print(error_result)

# Simulate repeated failures.
for attempt in range(3):
    retry_allowed = retry_manager.record_failure()

    print(f"\nAttempt: {attempt + 1}")
    print(f"Retry allowed: {retry_allowed}")
    print(f"Failed attempts: {retry_manager.get_attempt_count()}")
    print(f"Should stop: {retry_manager.should_stop()}")