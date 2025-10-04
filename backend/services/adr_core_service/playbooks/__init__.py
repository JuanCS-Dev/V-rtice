"""ADR Core Service - Playbooks Package.

This package is responsible for handling automated response playbooks.
It includes the loader for parsing YAML-based playbook definitions and
making them available to the Response Engine.
"""

from .loader import PlaybookLoader

__all__ = ['PlaybookLoader']