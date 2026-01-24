"""Logging configuration"""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory
from rich.logging import RichHandler


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
    # Silence third-party noise
    for lib in ["urllib3", "multipart", "httpx", "httpcore"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    # Base logging config
    level = getattr(logging, log_level.upper())
    handlers = []
    
    # 1. Rich Console Handler (Human Readable)
    rich_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False,
    )
    rich_handler.setLevel(level)
    handlers.append(rich_handler)
    
    # 2. JSON File Handler (Machine Readable)
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # Configure structlog for file output
        # We need to bridge standard logging to structlog for the file handler
        # But since we are using structlog.stdlib.LoggerFactory, we can just formatting in the handler
        
        # However, a cleaner way with structlog + standard logging is:
        # standard logging -> handlers. 
        # For file handler, we want JSON. For console, we want Rich.
        
        # Let's use structlog's ProcessorFormatter to handle this differentiation
        from structlog.stdlib import ProcessorFormatter
        
        # JSON Processor for File
        json_processor = ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ]
        )
        file_handler.setFormatter(json_processor)
        handlers.append(file_handler)

    # Configure Basic Config with our handlers
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )

    # Configure Structlog to wrap standard logger
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            # This is the key: if we are using standard logging, we want to render to something standard logging understands
            # If we used structlog directly for output, we'd use ConsoleRenderer or JSONRenderer here.
            # But we are delegating to standard logging handlers (Rich and File).
            # So we use ProcessorFormatter.wrap_for_formatter
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get a structured logger instance"""
    return structlog.get_logger(name)
