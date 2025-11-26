# api_client.py
import logging
import requests
from retry_handler import retry_with_time_limit

logger = logging.getLogger("automation")

API_USERS = "https://jsonplaceholder.typicode.com/users"
API_POSTS = "https://jsonplaceholder.typicode.com/posts"
API_TODOS = "https://jsonplaceholder.typicode.com/todos"


@retry_with_time_limit
def fetch_json(url):
    logger.info(f"[API] Fetching {url}")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()
