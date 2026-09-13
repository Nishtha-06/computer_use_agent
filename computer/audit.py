# this file records the actions performed by the computer use agent
# so that each execution can be reviewd later.

import json
from datetime import datetime
from pathlib import Path

# File where agent actions will be stored
AUDIT_FILE = Path("logs")/"audit.json"

def log_action(tool_name,arguments,result):
    """Record ine agent action in the audit log."""

    # Create the logs directory if it does not exist.
    AUDIT_FILE.parent.mkdir(exist_ok=True)

    #Create one audit record
    record = {
        "timestamp":datetime.now().isoformat(),
        "tool":tool_name,
        "arguments":arguments,
        "result":str(result),
    }

    # Load existing records if audit file already exists.
    if AUDIT_FILE.exists():
        try:
            with open(AUDIT_FILE,"r",encoding="utf-8") as file:
                records = json.load(file)
        except (json.JSONDecodeError,OSError):
            records = []
    else:
        records = []

    # Add the new record
    records.append(record)

    # Save the updated audit history.
    with open(AUDIT_FILE,"w",encoding="utf-8") as file:
        json.dump(records,file,indent=4)

if __name__ == "__main__":
    print("Audit logger loaded successfully.")