# success_body.py

def success_message(users_count, posts_count, todos_count, timestamp):
    return f"""
Hello,

Attached is your automated report.

Records generated:
- Users: {users_count}
- Posts: {posts_count}
- Todos: {todos_count}

Timestamp: {timestamp}

Regards,
Cofinity Systems
"""
