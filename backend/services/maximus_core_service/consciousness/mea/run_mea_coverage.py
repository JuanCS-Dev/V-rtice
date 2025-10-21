"""
Standalone MEA Coverage Runner - Solves import timing issue

The problem: pytest imports consciousness.mea during collection phase,
before coverage starts, causing all MEA modules to be "previously imported."

Solution: Clear sys.modules and reload after coverage starts.
"""

import sys
import os

# Set PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# CRITICAL: Remove any previously imported consciousness.mea modules
# This must happen BEFORE coverage starts
modules_to_remove = [
    key for key in list(sys.modules.keys())
    if key.startswith('consciousness.mea')
]
for mod in modules_to_remove:
    del sys.modules[mod]

# Also remove consciousness package to force clean import
if 'consciousness' in sys.modules:
    del sys.modules['consciousness']

# Now start coverage BEFORE any consciousness imports
import coverage

cov = coverage.Coverage(
    source=['consciousness/mea'],
    omit=['*/test_*.py', '*/__pycache__/*', '*/tests/*']
)
cov.start()

# NOW import and run pytest (modules will be imported fresh under coverage)
import pytest

result = pytest.main([
    '-xvs',
    'consciousness/mea/test_mea_100pct.py',
    '--tb=short',
    '-p', 'no:cacheprovider',  # Disable cache to avoid pre-import
    '-p', 'no:cov',  # Disable pytest-cov plugin (we're using coverage directly)
    '-o', 'addopts=',  # Override pytest.ini addopts to remove --cov arguments
])

# Stop coverage and report
cov.stop()
cov.save()

print('\n' + '=' * 80)
print('MEA COVERAGE REPORT')
print('=' * 80)
cov.report(show_missing=True)

# Exit with pytest's exit code
sys.exit(result)
