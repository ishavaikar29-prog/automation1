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
        "name": "usageReport",
        "method": "POST",
        "endpoint": "/api/usage/report",
        "params": {
            "start_date": "{start_date}",
            "end_date": "{end_date}"
        },
        "headers": {
            "Authorization": "Bearer {token}"
        }
    },
]
  
