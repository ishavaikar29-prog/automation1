API_FLOW_CONFIG = [
    {
        "name": "login",
        "method": "POST",
        "endpoint": "/api/v1/token",
        "body": {
            "username": "{username}",
            "password": "{password}",
            "bankName": "janaatasahakaribank"
        },
        "headers": {"Content-Type": "application/json"}
    },
    {
        "name": "LOGS",
        "method": "POST",
        "endpoint": "/api/log/download",
        "body": {
            "startDate": "2025-12-03",
            "endDate": "2025-12-03"
        },
        "headers": {"Authorization": "Bearer {token}"}
    }
]
