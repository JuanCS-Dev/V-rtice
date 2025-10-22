"""
Combined Safety Coverage Runner - Original + Missing Lines Tests
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

modules_to_remove = [
    key for key in list(sys.modules.keys())
    if key.startswith('consciousness')
]
for mod in modules_to_remove:
    del sys.modules[mod]

import coverage

cov = coverage.Coverage(
    source=['consciousness.safety'],
    omit=['*/test_*.py', '*/__pycache__/*', '*/tests/*']
)
cov.start()

import pytest

result = pytest.main([
    '-vs',
    'consciousness/test_safety_100pct.py',
    'consciousness/test_safety_missing_lines.py',
    '--tb=line',
    '-p', 'no:cacheprovider',
    '-p', 'no:cov',
    '-o', 'addopts=',
])

cov.stop()
cov.save()

print('\n' + '=' * 80)
print('SAFETY MODULE - COMBINED COVERAGE REPORT')
print('=' * 80)
cov.report(show_missing=True)

sys.exit(result)
