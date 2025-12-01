# error_handler.py
import logging

def init_logger():
    logger = logging.getLogger("automation")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if init_logger called multiple times
    if not logger.handlers:
        fh = logging.FileHandler("run.log", mode="w")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
