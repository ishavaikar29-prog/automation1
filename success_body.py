# success_body.py

def success_message(total_items, timestamp):
    return f"""
Hello,

The automated report has been generated successfully.

Total items collected across APIs: {total_items}

Timestamp: {timestamp}

Regards,
Cofinity Systems
"""
