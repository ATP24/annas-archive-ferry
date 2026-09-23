#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anna's Archive Ferry (安娜书渡) - Agent Skill CLI Runner
=========================================================
Lightweight entry point wrapper forwarding to annas_archive_ferry.engine.
Maintains full backward compatibility with Agent Skill directory conventions.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so annas_archive_ferry is importable without installation
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from annas_archive_ferry.engine import main

if __name__ == "__main__":
    sys.exit(main())
