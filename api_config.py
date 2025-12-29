API_FLOW_CONFIG = [
    {
        "name": "login",
        "method": "POST",
        "endpoint": "/v1/token",
        "body": {
            "userId": "{userId}",
            "password": "{password}",
            "bankName": "janaatasahakaribank"
        },
        "headers": {"Content-Type": "application/json"}
    },
    {
        "name": "LOGS",
        "method": "GET",
        "endpoint": "/api/report/logs",
        "params": {
            "startDate": "{startDate}",
            "endDate": "{endDate}"
        },
        "headers": {
            "Authorization": "Bearer {token}"
        }
    },
    {
        "name": "LOGS",
        "method": "POST",
        "endpoint": "/log/download",
        "body": {
            "startDate": "2025-12-03",
            "endDate": "2025-12-03"
        },
        "headers": {"Authorization": "Bearer {token}"}
    }
]
