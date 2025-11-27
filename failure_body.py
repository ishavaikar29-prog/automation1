# failure_body.py

def failure_message(errors, timestamp):
    msg = """
Hello,

The automated report failed due to the following errors:

"""
    for name, err in errors:
        msg += f"- {name}: {err}\n"

    msg += f"""

Timestamp: {timestamp}

Regards,
Cofinity Systems
"""
    return msg
