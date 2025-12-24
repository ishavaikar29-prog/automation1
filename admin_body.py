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
Cofinity System
"""

def admin_failure_message(failures, timestamp, summary=""):

    msg = f"""
Hello Admin,

The automated report FAILED.

Failure Summary:
{summary}

Errors Detected:
"""

    for name, err in failures:
        msg += f"- {name}: {err}\n"

    msg += f"""

This email contains:
- run.log only (Excel not generated)

Timestamp: {timestamp}

Regards,
Cofinity System
"""
    return msg
