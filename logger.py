import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

current_date = datetime.now().strftime("%Y-%m-%d")
log_filename = os.path.join(log_folder, f"ai_resume_{current_date}.log")

log_level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
log_level = getattr(logging, log_level_name, logging.INFO)

logger = logging.getLogger("AiResumeLogger")
logger.setLevel(log_level)

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_filename, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
