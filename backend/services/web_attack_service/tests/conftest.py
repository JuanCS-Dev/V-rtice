"""pytest configuration for web_attack_service tests.

Mock external dependencies before any test collection.
"""

import sys
from unittest.mock import Mock

# Mock external dependencies that may not be installed
sys.modules["zapv2"] = Mock()
sys.modules["google"] = Mock()
sys.modules["google.generativeai"] = Mock()
sys.modules["anthropic"] = Mock()
