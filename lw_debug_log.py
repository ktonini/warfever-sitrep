"""Central logger for alliance monitor (GUI + core)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import IO

LOGGER_NAME = "lw.monitor"


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def flush_monitor_log() -> None:
    """Push log handlers to disk (safe from worker threads)."""
    for h in get_logger().handlers:
        try:
            h.flush()
        except Exception:
            pass


def setup_monitor_logging(
    *,
    verbose: bool,
    log_file: Path | None,
    stream: IO[str] | None = None,
    gui_handler: logging.Handler | None = None,
) -> None:
    """Attach handlers to the lw.monitor logger (clears previous handlers)."""
    log = get_logger()
    log.handlers.clear()
    log.propagate = False
    level = logging.DEBUG if verbose else logging.INFO
    log.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        log.addHandler(fh)

    if stream is not None:
        sh = logging.StreamHandler(stream)
        sh.setLevel(logging.DEBUG if verbose else logging.WARNING)
        sh.setFormatter(fmt)
        log.addHandler(sh)

    if gui_handler is not None:
        gui_handler.setFormatter(fmt)
        gui_handler.setLevel(level)
        log.addHandler(gui_handler)
