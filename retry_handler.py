# retry_handler.py
import time
import logging
import requests

MAX_TOTAL_RETRY_SECONDS = 30
INITIAL_DELAY = 1
BACKOFF = 2
MAX_ATTEMPTS = 6

logger = logging.getLogger("automation")

def retry_with_time_limit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        attempt = 0
        delay = INITIAL_DELAY
        last_exc = None

        while True:
            attempt += 1
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                last_exc = e
                elapsed = time.time() - start
                remaining = MAX_TOTAL_RETRY_SECONDS - elapsed

                logger.error(f"[RETRY] Attempt {attempt} failed: {e}")

                if attempt >= MAX_ATTEMPTS or remaining <= 0:
                    logger.error("Retry window exhausted. Giving up.")
                    break

                sleep_for = min(delay, remaining)
                logger.info(f"[RETRY] Sleeping {sleep_for}s…")
                time.sleep(sleep_for)
                delay *= BACKOFF
            except Exception as e:
                logger.error(f"Permanent error: {e}")
                raise

        raise last_exc
    return wrapper
