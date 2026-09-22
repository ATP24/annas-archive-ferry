"""
Anna's Archive Ferry (安娜书渡)
================================
Automated retrieval, disambiguation, neural OCR, and streaming ferry engine for Anna's Archive.

Licensed under MIT. Copyright (c) 2026 ATP24.
"""

__version__ = "1.1.0"
__author__ = "ATP24"

from .config import load_config, get_config_value, save_dynamic_config
from .engine import (
    search_books,
    probe_book,
    download_book,
    run_doctor,
    main
)

__all__ = [
    "__version__",
    "__author__",
    "load_config",
    "get_config_value",
    "save_dynamic_config",
    "search_books",
    "probe_book",
    "download_book",
    "run_doctor",
    "main",
]
