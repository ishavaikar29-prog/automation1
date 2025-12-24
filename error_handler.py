# error_handler.py
import logging
import os

def init_logger():
    logger = logging.getLogger("automation")
    logger.setLevel(logging.DEBUG)

    # Create file handler
    fh = logging.FileHandler("run.log", mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Add detailed log formatting
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d in %(funcName)s() | %(message)s"
    )
    fh.setFormatter(formatter)

    # Prevent duplicate handlers
    if not logger.handlers:
        logger.addHandler(fh)

    return logger
