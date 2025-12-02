# api_config.py
# Put all method/body/params/headers and order here.
# URLs will be provided via environment variables API_1_URL, API_2_URL, ...

API_FLOW_CONFIG = [
    {
        "name": "API_1_URL",
        "method": "POST",
        "body": { "bankDomainName": "testbankt1"},
        "params": {},
        "headers": {"Content-Type": "application/json"}
    }
]

# Edit this file to add/remove steps or modify body/params/headers/method.
# Methods should be uppercase strings like "GET", "POST", etc.
