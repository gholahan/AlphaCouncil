"""Centralized logging configuration with safe cleanup."""

import logging
import sys
import atexit
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class LogManager:
    """Manages application logging with safe cleanup."""

    _instance: Optional["LogManager"] = None
    _initialized: bool = False
    _handlers: list = []

    def __new__(cls):
        """Singleton pattern to ensure one log manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def setup_logging(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        enable_json: bool = False,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
    ) -> logging.Logger:
        """
        Setup application-wide logging.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            log_format: Custom log format string
            enable_json: Enable JSON formatted logs
            max_bytes: Max size per log file before rotation
            backup_count: Number of backup files to keep

        Returns:
            Root logger instance
        """
        if self._initialized:
            return logging.getLogger()

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Default format
        if log_format is None:
            log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if enable_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    log_format,
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )

        root_logger.addHandler(console_handler)
        self._handlers.append(console_handler)

        # File handler with rotation
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))

            if enable_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        log_format,
                        datefmt="%Y-%m-%d %H:%M:%S"
                    )
                )

            root_logger.addHandler(file_handler)
            self._handlers.append(file_handler)

        # Silence noisy libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)

        self._initialized = True

        # Register cleanup on exit
        atexit.register(self.cleanup)

        root_logger.info(
            f"Logging initialized: level={log_level}, file={log_file}, json={enable_json}"
        )

        return root_logger

    def cleanup(self):
        """Safely cleanup logging handlers on shutdown."""
        if not self._initialized:
            return

        root_logger = logging.getLogger()

        try:
            root_logger.info("Shutting down logging system...")

            # Flush and close all handlers
            for handler in self._handlers:
                try:
                    handler.flush()
                    handler.close()
                except Exception as e:
                    # Use print as logging might be dead
                    print(f"Error closing handler: {e}", file=sys.stderr)

            # Remove handlers from root logger
            root_logger.handlers.clear()
            self._handlers.clear()

        except Exception as e:
            print(f"Error during logging cleanup: {e}", file=sys.stderr)
        finally:
            self._initialized = False

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger with the specified name.

        Args:
            name: Logger name (usually __name__)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)


# Global log manager instance
log_manager = LogManager()


def setup_logging_from_settings():
    """Initialize logging from settings configuration."""
    try:
        from src.config.settings import get_settings
    except ImportError:
        from config.settings import get_settings

    settings = get_settings()

    return log_manager.setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file=settings.LOG_FILE,
        log_format=settings.LOG_FORMAT,
        enable_json=settings.LOG_JSON,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return log_manager.get_logger(name)
