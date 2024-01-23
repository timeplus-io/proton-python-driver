import os
import sys

from loguru import logger

log_level = os.environ.get("APP_LOG_LEVEL", "INFO")

logger.remove()

logger.add(
    sys.stdout,
    colorize=True,
    format="{time} - {level} - {message}",
    level=log_level,
)
logger.add("app.log", rotation="500 MB", level=log_level)


def getLogger():
    return logger
