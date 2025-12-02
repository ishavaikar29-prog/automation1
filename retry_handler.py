# retry_handler.py
import time
import functools
import logging

logger = logging.getLogger("automation")

def retry_with_time_limit(max_attempts=3, initial_delay=1.0, backoff=2.0, total_timeout=30.0):
    """
    Decorator factory that retries the wrapped function up to max_attempts or until total_timeout reached.
    Usage:
      @retry_with_time_limit()
      def fn(...): ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            attempt = 0
            delay = initial_delay
            last_exc = None

            while attempt < max_attempts:
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    attempt += 1
                    elapsed = time.time() - start
                    if elapsed + delay > total_timeout or attempt >= max_attempts:
                        logger.error(f"[RETRY] Giving up after attempt {attempt}: {e}")
                        raise
                    logger.warning(f"[RETRY] attempt {attempt} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff
            # if we exit loop
            raise last_exc
        return wrapper
    return decorator
