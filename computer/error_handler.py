# This file provides basic error handling utilities for the
# Computer Use Agent
# It converts execution error into structured results so the
# agent can decide what to do next.

def handle_tool_error(tool_name: str,error: Exception):
    """Create a structured error result for a failed tool."""

    return {
        "status":"error",
        "tool":tool_name,
        "error":str(error)
    }

def is_error(result):
    """Return True when a tool result represents an error."""
    return isinstance(result,dict) and result.get("status") == "error"