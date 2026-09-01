"""
Centralized structured logger for Linny.
Supports console output and in-memory ring-buffer for live GUI log views.
"""

from __future__ import annotations

import logging
import sys
from collections import deque
from typing import Callable, List, Optional


class LinnyLogHandler(logging.Handler):
    """Memory ring-buffer handler to power the live dashboard console."""

    def __init__(self, capacity: int = 200) -> None:
        super().__init__()
        self.capacity = capacity
        self.records: deque[str] = deque(maxlen=capacity)
        self.callbacks: List[Callable[[str], None]] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.records.append(msg)
            for cb in self.callbacks:
                try:
                    cb(msg)
                except Exception:
                    pass
        except Exception:
            self.handleError(record)

    def add_callback(self, callback: Callable[[str], None]) -> None:
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str], None]) -> None:
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def get_recent_logs(self) -> List[str]:
        return list(self.records)


_memory_handler = LinnyLogHandler(capacity=250)
_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """Initialize Linny's root logging handlers and silence noisy libraries."""
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Memory handler for UI
    _memory_handler.setFormatter(formatter)
    _memory_handler.setLevel(level)

    root_logger = logging.getLogger("linny")
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(_memory_handler)

    # Suppress verbose 3rd party loggers
    for noisy in [
        "googleapiclient",
        "googleapiclient.discovery_cache",
        "googleapiclient.discovery",
        "urllib3",
        "PIL",
        "kasa",
        "comtypes",
        "comtypes._comobject",
        "comtypes._vtbl",
        "comtypes.client._managing",
        "comtypes._post_coinit",
        "pygame",
        "edge_tts",
    ]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Retrieve a child logger under the 'linny' namespace."""
    if not _configured:
        setup_logging()
    if name:
        return logging.getLogger(f"linny.{name}")
    return logging.getLogger("linny")


def get_memory_log_handler() -> LinnyLogHandler:
    """Access the global memory log handler."""
    if not _configured:
        setup_logging()
    return _memory_handler
