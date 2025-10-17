"""Test branch 162->exit for audit_logger.py via subprocess isolation.

This test MUST run in a completely isolated Python process to ensure
coverage.py tracks the branch correctly.
"""

import subprocess
import sys
import json
from pathlib import Path


class TestBranch162ExitIsolated:
    """Test the elusive branch 162->exit via subprocess."""
    
    def test_branch_162_exit_subprocess(self):
        """Test FAIL_OPEN=False raises exception - covers branch 162->exit.
        
        Runs in isolated subprocess to ensure coverage tracking works.
        """
        # Create isolated test script that starts coverage BEFORE import
        # CRITICAL: The exception must propagate to exit to cover branch 162->exit
        test_script = """
import sys
import os
import atexit

# Start coverage FIRST before any imports
import coverage
cov = coverage.Coverage(
    branch=True,
    source=['backend/shared'],
    omit=['*/tests/*', '*/test_*']
)
cov.start()

# Register coverage save on exit (even on exception)
def save_coverage():
    cov.stop()
    cov.save()
    cov.json_report(outfile='/tmp/coverage_branch_162.json')

atexit.register(save_coverage)

# Now ensure PYTHONPATH and import
sys.path.insert(0, '/home/juan/vertice-dev')

from unittest.mock import Mock

# Import the module AFTER coverage started
import backend.shared.audit_logger as audit_module

# Configure for failure
audit_module.POSTGRES_AVAILABLE = True
mock_pg = Mock()
mock_pg.connect.side_effect = RuntimeError("Test error - branch 162")
audit_module.psycopg2 = mock_pg
audit_module.AuditConfig.FAIL_OPEN = False

# This MUST raise and propagate to exit to cover branch 162->exit
# DO NOT catch the exception - let it propagate
logger = audit_module.AuditLogger(log_to_file=False)

# If we get here, test failed
print("FAIL: No exception raised!")
sys.exit(1)
"""
        
        # Run in subprocess
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            cwd='/home/juan/vertice-dev'
        )
        
        # Verify execution
        assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
        assert "SUCCESS" in result.stdout, f"Branch not executed: {result.stdout}"
        
        # Verify coverage data was created
        coverage_file = Path('/tmp/coverage_branch_162.json')
        assert coverage_file.exists(), "Coverage JSON not created"
        
        # Load and verify branch was covered
        with open(coverage_file) as f:
            data = json.load(f)
            audit_file = data['files'].get('backend/shared/audit_logger.py', {})
            missing_branches = audit_file.get('missing_branches', [])
            
            # Branch 162->exit should NOT be in missing anymore
            branch_162_missing = [162, -136] in missing_branches
            
            assert not branch_162_missing, \
                f"Branch 162->exit still missing! Missing branches: {missing_branches}"
