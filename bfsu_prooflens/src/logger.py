# -*- coding: utf-8 -*-
"""Logging setup."""
from __future__ import annotations

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from .utils import writable_path, ensure_runtime_dirs


def setup_logger() -> logging.Logger:
    ensure_runtime_dirs()
    logger = logging.getLogger("bfsu_prooflens")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_path: Path = writable_path("logs/app.log")
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    return logger


logger = setup_logger()
