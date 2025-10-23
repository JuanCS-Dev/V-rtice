"""
Pytest configuration for async tests
"""

import sys
from pathlib import Path

# Add parent directory to sys.path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

