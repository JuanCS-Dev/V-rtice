"""
Pytest configuration for MIP tests.

Configura paths e fixtures para testes do Motor de Integridade Processual.
"""

import sys
from pathlib import Path

# Add parent directory to path para permitir imports relativos
mip_root = Path(__file__).parent.parent
backend_root = mip_root.parent.parent

# Add both paths
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
if str(mip_root) not in sys.path:
    sys.path.insert(0, str(mip_root))
