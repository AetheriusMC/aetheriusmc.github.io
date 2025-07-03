"""
Logging utilities and configuration.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

import structlog


def setup_logging(config) -> None:
    """Setup application logging configuration."""
    
    # Create logs directory if it doesn't exist
    log_file = Path(config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    # Configure structlog
    setup_structlog()


def configure_logger_levels():
    """Configure log levels for specific loggers."""
    logger_configs = {
        "uvicorn": logging.INFO,
        "uvicorn.access": logging.WARNING,
        "fastapi": logging.INFO,
        "sqlalchemy.engine": logging.WARNING,
        "redis": logging.WARNING,
        "websockets": logging.INFO,
    }
    
    for logger_name, level in logger_configs.items():
        logging.getLogger(logger_name).setLevel(level)


def setup_structlog():
    """Setup structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)