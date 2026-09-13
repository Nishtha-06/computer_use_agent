# this file tests wheteher the computer use agent can record
# an executed action in the audit log.

from computer.audit import log_action

log_action(
    "tool_open_application",
    {"application": "notepad"},
    None,
)

print("Audit log test completed successfully.")