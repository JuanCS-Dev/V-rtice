"""Test branch 164->exit for audit_logger.py - ABSOLUTE FINAL.

This test specifically targets the branch 164->exit which is a re-raise
inside the except block of __init__.
"""

import pytest


class TestBranch164ExitAbsolute:
    """Test the branch 164->exit (re-raise in __init__ except block)."""
    
    def test_branch_163_to_165_fail_open_true(self):
        """Test FAIL_OPEN=True with exception - covers branch 163->165 (pass).
        
        This covers the "degraded mode" path where DB connection fails
        but we continue anyway because FAIL_OPEN=True.
        """
        import sys
        from unittest.mock import Mock, patch
        
        # Clean import
        if 'backend.shared.audit_logger' in sys.modules:
            del sys.modules['backend.shared.audit_logger']
        
        import backend.shared.audit_logger as audit_module
        
        # Save originals
        orig_postgres = audit_module.POSTGRES_AVAILABLE
        orig_fail_open = audit_module.AuditConfig.FAIL_OPEN
        
        try:
            # Configure
            audit_module.POSTGRES_AVAILABLE = True
            audit_module.AuditConfig.FAIL_OPEN = True  # KEY: True means continue on error
            
            # Mock psycopg2 to raise exception
            with patch.object(audit_module, 'psycopg2') as mock_pg:
                mock_pg.connect.side_effect = RuntimeError("DB error - degraded mode")
                
                # This should:
                # 1. Call _connect_db() from __init__
                # 2. Exception raised, caught in except block
                # 3. if AuditConfig.FAIL_OPEN: (line 163) = True
                # 4. pass (line 165) - THIS IS BRANCH 163->165
                # 5. Continue without raising
                
                logger = audit_module.AuditLogger(log_to_file=False)
                
                # Verify we're in degraded mode (no DB)
                assert logger.db_connection is None
                
        finally:
            # Restore
            audit_module.POSTGRES_AVAILABLE = orig_postgres
            audit_module.AuditConfig.FAIL_OPEN = orig_fail_open
    
    def test_branch_164_exit_reraise_in_except(self):
        """Test that covers branch 164->exit via re-raise in except block.
        
        The key is to make __init__ catch an exception from _connect_db()
        and then re-raise it when FAIL_OPEN=False.
        """
        import sys
        from unittest.mock import Mock, patch
        
        # Clean import
        if 'backend.shared.audit_logger' in sys.modules:
            del sys.modules['backend.shared.audit_logger']
        
        import backend.shared.audit_logger as audit_module
        
        # Save originals
        orig_fail_open = audit_module.AuditConfig.FAIL_OPEN
        orig_postgres = audit_module.POSTGRES_AVAILABLE
        
        try:
            # Configure
            audit_module.POSTGRES_AVAILABLE = True
            audit_module.AuditConfig.FAIL_OPEN = False
            
            # Mock psycopg2 to raise exception in _connect_db
            with patch.object(audit_module, 'psycopg2') as mock_pg:
                mock_pg.connect.side_effect = RuntimeError("DB connection failed")
                
                # This should:
                # 1. Call _connect_db() from __init__ (line 159)
                # 2. _connect_db raises RuntimeError (caught at line 160)
                # 3. except block (line 160-165)
                # 4. logging.error (line 161)
                # 5. fail_open = AuditConfig.FAIL_OPEN  (line 163) = False
                # 6. if not fail_open: (line 164) = True
                # 7. raise (line 165) - THIS IS THE BRANCH 164->exit
                
                with pytest.raises(RuntimeError, match="DB connection failed"):
                    audit_module.AuditLogger(log_to_file=False)
                    
        finally:
            # Restore
            audit_module.AuditConfig.FAIL_OPEN = orig_fail_open
            audit_module.POSTGRES_AVAILABLE = orig_postgres
