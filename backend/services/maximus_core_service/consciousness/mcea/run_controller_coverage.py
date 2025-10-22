"""
Standalone MCEA Controller Coverage Runner - Solves import timing issue

The problem: pytest imports consciousness.mcea during collection phase,
before coverage starts, causing the controller module to be "previously imported."

Solution: Clear sys.modules and reload after coverage starts.
"""

import sys
import os

# Set PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# CRITICAL: Remove any previously imported consciousness.mcea modules
# This must happen BEFORE coverage starts
modules_to_remove = [
    key for key in list(sys.modules.keys())
    if key.startswith('consciousness.mcea') or key.startswith('consciousness')
]
for mod in modules_to_remove:
    del sys.modules[mod]

# Now start coverage BEFORE any consciousness imports
import coverage

cov = coverage.Coverage(
    source=['consciousness.mcea.controller'],
    omit=['*/test_*.py', '*/__pycache__/*', '*/tests/*']
)
cov.start()

# NOW import and run pytest (modules will be imported fresh under coverage)
import pytest

result = pytest.main([
    '-vs',  # Removed -x to run all tests even if one fails
    'consciousness/mcea/test_controller_100pct.py',
    '--tb=short',
    '-p', 'no:cacheprovider',  # Disable cache to avoid pre-import
    '-p', 'no:cov',  # Disable pytest-cov plugin (we're using coverage directly)
    '-o', 'addopts=',  # Override pytest.ini addopts to remove --cov arguments
])

# Stop coverage and report
cov.stop()
cov.save()

print('\n' + '=' * 80)
print('MCEA CONTROLLER COVERAGE REPORT')
print('=' * 80)
cov.report(show_missing=True)

# Exit with pytest's exit code
sys.exit(result)
