"""Pytest configuration for wargaming_crisol tests.

Ensures proper module imports.
"""
import sys
import os

# Add wargaming_crisol to Python path
service_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)
