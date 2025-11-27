# admin_body.py

def admin_success_message(timestamp):
    return f"""
Hello Admin,

The automated report has been successfully generated.

This email contains:
- Excel report
- run.log file (execution log)

Timestamp: {timestamp}

Regards,
Automation System
"""

def admin_failure_message(errors, timestamp):
    msg = """
Hello Admin,

The automated report FAILED.

Errors:
"""
    for name, err in errors:
        msg += f"- {name}: {err}\n"

    msg += f"""

This email contains:
- run.log file only (Excel not generated)

Timestamp: {timestamp}

Regards,
Cofinity System
"""
    return msg
