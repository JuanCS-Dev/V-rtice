"""Test configuration for Atlas Service."""

import sys
from pathlib import Path

# Fix import path - ensure we import from atlas_service, not other services
service_dir = Path(__file__).parent.parent
sys.path.insert(0, str(service_dir))
