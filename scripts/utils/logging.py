"""
Logging utilities for timeline scripts
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


def setup_logger(
    name: str = 'timeline',
    log_file: Optional[str] = None,
    level: str = 'INFO',
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string for log messages
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Default format
    if not format_string:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Console handler with color
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    COLORS = {
        'DEBUG': Colors.GRAY,
        'INFO': Colors.BLUE,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA,
    }
    
    def format(self, record):
        # Add color to the level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.RESET}"
        
        # Format the message
        result = super().format(record)
        
        # Reset levelname for file output
        record.levelname = levelname
        
        return result


# Convenience functions for common logging patterns
def log_info(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an info message."""
    if logger:
        logger.info(message)
    else:
        print(f"{Colors.BLUE}ℹ{Colors.RESET}  {message}")


def log_warning(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a warning message."""
    if logger:
        logger.warning(message)
    else:
        print(f"{Colors.YELLOW}⚠{Colors.RESET}  {message}")


def log_error(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an error message."""
    if logger:
        logger.error(message)
    else:
        print(f"{Colors.RED}✗{Colors.RESET}  {message}", file=sys.stderr)


def log_success(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a success message."""
    if logger:
        logger.info(f"✓ {message}")
    else:
        print(f"{Colors.GREEN}✓{Colors.RESET}  {message}")


def print_header(title: str, width: int = 60) -> None:
    """Print a formatted header."""
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def print_summary(stats: dict, title: str = "Summary") -> None:
    """
    Print a formatted summary of statistics.
    
    Args:
        stats: Dictionary of statistics to display
        title: Title for the summary section
    """
    print(f"\n{Colors.CYAN}{title}{Colors.RESET}")
    print("-" * 40)
    
    for key, value in stats.items():
        # Format the key (replace underscores with spaces, title case)
        formatted_key = key.replace('_', ' ').title()
        
        # Color code based on value type or key
        if isinstance(value, bool):
            value_str = f"{Colors.GREEN}Yes{Colors.RESET}" if value else f"{Colors.RED}No{Colors.RESET}"
        elif 'error' in key.lower() or 'fail' in key.lower():
            value_str = f"{Colors.RED}{value}{Colors.RESET}" if value else f"{Colors.GREEN}{value}{Colors.RESET}"
        elif 'success' in key.lower() or 'pass' in key.lower():
            value_str = f"{Colors.GREEN}{value}{Colors.RESET}" if value else f"{Colors.RED}{value}{Colors.RESET}"
        else:
            value_str = str(value)
        
        print(f"  {formatted_key}: {value_str}")
    
    print("-" * 40)


def progress_bar(current: int, total: int, width: int = 50, prefix: str = "") -> None:
    """
    Display a progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        width: Width of the progress bar
        prefix: Optional prefix text
    """
    if total == 0:
        percent = 100
    else:
        percent = (current / total) * 100
    
    filled = int(width * current // total) if total > 0 else width
    bar = '█' * filled + '░' * (width - filled)
    
    sys.stdout.write(f'\r{prefix} [{bar}] {percent:.1f}% ({current}/{total})')
    sys.stdout.flush()
    
    if current >= total:
        print()  # New line when complete