import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from config.settings import LOGS_DIR

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance that writes to a timed rotating file
    (retained for 7 days) as well as the console.
    """
    logger = logging.getLogger(name)
    
    # Only configure if the logger doesn't have handlers yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        
        # 1. Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 2. Daily Rotating File Handler (Keeps 7 days)
        log_file = LOGS_DIR / "app.log"
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger
