"""Logging configuration for media article writer."""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "media_article_writer",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """Set up and configure logger.
    
    Args:
        name: Logger name (use "" for root logger)
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        console_output: Whether to output to console (default: True)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Update existing handlers' levels if logger already has handlers
    if logger.handlers:
        for handler in logger.handlers:
            handler.setLevel(level)
        logger.setLevel(level)  # Also update logger level
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Ensure child loggers propagate to this logger (default is True, but be explicit)
    logger.propagate = True
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance.
    
    Args:
        name: Logger name (default: "media_article_writer")
        
    Returns:
        Logger instance
    """
    if name is None:
        name = "media_article_writer"
    logger = logging.getLogger(name)
    # Ensure child loggers propagate to root logger
    logger.propagate = True
    return logger
