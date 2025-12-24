import logging
import os

def init_logger():
    logger = logging.getLogger("automation")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler("run.log", mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Log format with timestamp, level, file, line, function
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d in %(funcName)s() | %(message)s"
    )

    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
