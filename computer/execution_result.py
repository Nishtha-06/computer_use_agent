# This file defines helper functions for creating structured
# exection results for the computer Use Agent

def success_result(tool_name: str,result=None):
    """Create a successful tool exection result."""

    return {
        "status":"success",
        "tool":tool_name,
        "result":result,
    }

def denied_result(tool_name:str):
    """Create a result for an action denied by the user."""
    return {
        "status":"denied",
        "tool":tool_name
    }

def is_success(result):
    """Return True when a tool execution was successful."""
    return isinstance(result,dict) and result.get("status") == "success"

def is_denied(result):
    """Return True when the user denied an action."""
    return isinstance(result,dict) and result.get("status") == "denied"
