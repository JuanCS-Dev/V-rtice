"""Test module metadata coverage."""
import sys
from pathlib import Path

# Add parent service to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import __init__ as command_bus_module


def test_module_version():
    """Test module exports __version__."""
    assert hasattr(command_bus_module, "__version__")
    assert isinstance(command_bus_module.__version__, str)
    assert command_bus_module.__version__ == "1.0.0"
