#!/usr/bin/env python3
"""
English Trainer v7.0 - Main Entry Point
A modern, modular English learning application powered by LLMs.
"""

import sys
from pathlib import Path

# Add the parent directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from english_trainer.core.app import main

if __name__ == "__main__":
    sys.exit(main())