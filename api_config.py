# api_config.py
# Put all method/body/params/headers and order here.
# URLs will be provided via environment variables API_1_URL, API_2_URL, ...

API_FLOW_CONFIG = [
    {
        "name": "login",
        "method": "POST",
        "body": {"username": "myuser", "password": "mypassword"},
        "params": {},
        "headers": {"Content-Type": "application/json"}
    },
    {
        "name": "users",
        "method": "GET",
        "body": {},
        "params": {"limit": "100"},
        "headers": {"Authorization": "Bearer {token}"}
    },
    {
        "name": "transactions",
        "method": "GET",
        "body": {},
        "params": {},
        "headers": {"Authorization": "Bearer {token}"}
    }
]

# Edit this file to add/remove steps or modify body/params/headers/method.
# Methods should be uppercase strings like "GET", "POST", etc.
