import os
import logging
from datetime import datetime

_logger_instance = None  # 保证只初始化一次

def _ensure_log_dir():
    home_dir = os.path.expanduser("~")
    log_dir = os.path.join(home_dir, ".FreeShell", "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def _init_logger():
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    log_dir = _ensure_log_dir()
    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger("freeshell_logger")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger

def log_info(message):
    logger = _init_logger()
    logger.info(message)

def log_warning(message):
    logger = _init_logger()
    logger.warning(message)

def log_error(message):
    logger = _init_logger()
    logger.error(message)
