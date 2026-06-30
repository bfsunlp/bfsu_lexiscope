# -*- coding: utf-8 -*-
"""BFSU ProofLens entry point."""
from __future__ import annotations

import multiprocessing

from src.app import main

if __name__ == "__main__":
    # Required for optional ProcessPoolExecutor support on Windows and in
    # PyInstaller-frozen builds.
    multiprocessing.freeze_support()
    main()
