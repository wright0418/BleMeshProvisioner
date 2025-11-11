"""
Logger module for consistent logging across the SDK.

Provides configured logger instances with file and console output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Setup a logger with file and/or console handlers.

    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, no file logging
        console: Whether to output to console

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Connection established")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
