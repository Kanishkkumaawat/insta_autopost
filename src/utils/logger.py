"""Logging configuration"""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory


def setup_logger(
    log_level: str = "INFO",
    log_format: str = "json",
    file_path: Optional[str] = None,
    max_bytes: int = 10485760,
    backup_count: int = 5,
) -> None:
    """
    Configure structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format (json, console)
        file_path: Path to log file
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    # Set up handlers
    handlers = []
    
    # Create logs directory if needed
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up file handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        handlers.append(file_handler)
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    handlers.append(console_handler)
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
    )


def get_logger(name: str = __name__):
    """Get a structured logger instance"""
    return structlog.get_logger(name)
