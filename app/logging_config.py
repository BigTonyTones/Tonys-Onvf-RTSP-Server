"""
Logging configuration for Tonys Onvif-RTSP Server.

This module provides structured logging with colored console output
and environment-based log level configuration.
"""

import logging
import os
import sys


# ANSI color codes for console output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Log level colors
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log levels for console output.
    """

    LEVEL_COLORS = {
        logging.DEBUG: Colors.DEBUG,
        logging.INFO: Colors.INFO,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.ERROR,
        logging.CRITICAL: Colors.CRITICAL,
    }

    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and self._supports_color()

    def _supports_color(self):
        """Check if the terminal supports color output."""
        # Check for NO_COLOR environment variable (standard)
        if os.environ.get('NO_COLOR'):
            return False

        # Check if stdout is a TTY
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False

        # Windows requires special handling
        if sys.platform == 'win32':
            try:
                # Try to enable ANSI colors on Windows 10+
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False

        return True

    def format(self, record):
        """Format the log record with optional colors."""
        # Save original levelname
        original_levelname = record.levelname

        if self.use_colors:
            color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
            record.levelname = f"{color}{record.levelname}{Colors.RESET}"

        result = super().format(record)

        # Restore original levelname
        record.levelname = original_levelname

        return result


def get_log_level():
    """
    Get the log level from environment variable LOG_LEVEL.
    Defaults to INFO if not set or invalid.
    """
    level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()

    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    return level_map.get(level_name, logging.INFO)


def setup_logging():
    """
    Set up the root logger with console handler and colored output.
    This should be called once at application startup.
    """
    # Get the log level from environment
    log_level = get_log_level()

    # Create formatter with timestamp, level, module name, and message
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = ColoredFormatter(fmt=log_format, datefmt=date_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('zeep').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


# Module-level flag to track if logging has been set up
_logging_configured = False


def get_logger(name):
    """
    Get a logger for the specified module name.

    This function also ensures logging is configured on first call.

    Args:
        name: The name for the logger, typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.

    Example:
        from .logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    global _logging_configured

    if not _logging_configured:
        setup_logging()
        _logging_configured = True

    return logging.getLogger(name)
