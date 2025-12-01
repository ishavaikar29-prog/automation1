# api_client.py
import logging
import requests
import json
from retry_handler import retry_with_time_limit

logger = logging.getLogger("automation")


@retry_with_time_limit
def call_api(method, url, params=None, body=None, headers=None, timeout=15):
    """
    Generic API caller supporting GET, POST, PUT, PATCH, DELETE.
    Returns JSON (or raises).
    """
    method = method.upper()
    logger.info(f"[API] Calling {method} {url}")

    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=body,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        logger.info(f"[API] Success {method} {url} (status={response.status_code})")

        # try to decode JSON; if empty return None
        if response.text:
            return response.json()
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"[API] Error {method} {url}: {e}")
        raise


def run_api_flow(api_flow):
    """
    Accepts a list of steps (each step from api_config merged with URL from env).
    Each step is a dict: {name, method, url, headers, params, body}
    Returns: dict mapping step name -> response (json or None).
    Auto-extracts "token" from JSON responses and injects into later steps using {token}.
    """
    results = {}
    shared = {}  # for token or other extracted values

    for step in api_flow:
        name = step["name"]
        method = step["method"]
        url = step["url"]
        params = step.get("params") or {}
        body = step.get("body") or {}
        headers = step.get("headers") or {}

        logger.info(f"[FLOW] Executing step: {name} -> {method} {url}")

        # Replace placeholders from shared store (like {token}) in url/headers/params/body
        if shared.get("token"):
            token = shared["token"]
            if isinstance(url, str):
                url = url.replace("{token}", token)

            headers = {
                k: (v.replace("{token}", token) if isinstance(v, str) else v)
                for k, v in headers.items()
            }

            params = {
                k: (v.replace("{token}", token) if isinstance(v, str) else v)
                for k, v in params.items()
            }

            # body may be nested; replace string occurrences at top-level strings
            if isinstance(body, dict):
                body = {
                    k: (v.replace("{token}", token) if isinstance(v, str) else v)
                    for k, v in body.items()
                }

        # call the API
        resp = call_api(method=method, url=url, params=params, body=body, headers=headers)
        results[name] = resp

        # if response is dict and contains "token" extract it
        if isinstance(resp, dict):
            if "token" in resp:
                shared["token"] = resp["token"]

    return results
