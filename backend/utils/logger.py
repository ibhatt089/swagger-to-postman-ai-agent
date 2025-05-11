"""
Structured logger for the Swagger-to-Postman AI Agent.

- Console logging (rich formatting)
- Rotating file logging
- Custom SUCCESS level (25)
- Supports ENV override: AGENT_LOG_LEVEL = DEBUG / INFO / SUCCESS / etc.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler
from rich.console import Console

from backend.utils.constants import LOG_DIR, LogLevel

# === Register Custom SUCCESS Log Level ===
logging.addLevelName(LogLevel.SUCCESS, "SUCCESS")


def success(self, message, *args, **kwargs):
    """Custom SUCCESS level log method."""
    if self.isEnabledFor(LogLevel.SUCCESS):
        self._log(LogLevel.SUCCESS, message, args, **kwargs)


# Attach custom method to the logger
logging.Logger.success = success


class LoggerFactory:
    """
    Factory for creating Rich + File rotating loggers.

    Uses ENV config for AGENT_LOG_LEVEL.
    """

    @staticmethod
    def get_logger(name: str = "SwaggerToPostmanAgent", log_to_file: Optional[bool] = True) -> logging.Logger:
        """
        Returns a logger with RichHandler and RotatingFileHandler.

        Args:
            name (str): Name of the logger instance.
            log_to_file (Optional[bool]): Enable writing logs to disk.

        Returns:
            logging.Logger: Configured logger instance.
        """
        _logger = logging.getLogger(name)
        if _logger.handlers:
            return _logger

        # Pull ENV-configured log level or default to INFO
        env_level = os.getenv("AGENT_LOG_LEVEL", "INFO").upper()
        log_level = getattr(LogLevel, env_level, LogLevel.INFO)

        _logger.setLevel(log_level)

        # === Console Logger ===
        console_handler = RichHandler(
            console=Console(),
            markup=True,
            show_time=True,
            show_path=False,
            rich_tracebacks=True
        )
        console_handler.setLevel(log_level)
        _logger.addHandler(console_handler)

        # === File Logger ===
        if log_to_file:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                filename=Path(LOG_DIR) / "agent_runtime.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=2
            )
            file_handler.setLevel(LogLevel.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s — %(levelname)s — %(name)s — %(message)s'
            ))
            _logger.addHandler(file_handler)

        return _logger


# === Default Global Logger Instance ===
logger = LoggerFactory.get_logger()
