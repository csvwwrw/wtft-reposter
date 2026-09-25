"""
Logging configuration module setting up root and module-level loggers
with file rotation and console output.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path
from config import Config

def setup_logging(
    log_level=Config.LOG_LEVEL,
    log_file=str(Config.LOG_FILE),
    console=True
) -> None:
    """
    Configure the root logger with a rotating file handler and optional
    console stream output.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    target_level = getattr(logging, str(log_level).upper(), logging.INFO)
    root_logger.setLevel(target_level)

    for existing_handler in root_logger.handlers[:]:
        existing_handler.close()
        root_logger.removeHandler(existing_handler)

    formatter = logging.Formatter(
        fmt=Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    )

    file_handler = TimedRotatingFileHandler(
        filename=str(log_path),
        when='W0',
        interval=1,
        backupCount=1,
        encoding='utf-8',
        delay=False,
    )
    file_handler.setLevel(target_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(target_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    for noisy_lib in ('urllib3', 'telebot', 'playwright'):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)

    root_logger.info(f'Logging configured: {log_file} (level={log_level})')

def get_module_logger(module_name:str) -> logging.Logger:
    """
    Retrieve a logger instance bound to a specific module name.
    """
    return logging.getLogger(module_name)