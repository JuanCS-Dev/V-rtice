"""Test import-time coverage for audit_logger.py - covers lines 86-89.

This MUST run in isolation to capture module-level import error handling.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock


class TestPsycopg2ImportError:
    """Test psycopg2 ImportError at module load time - covers lines 86-89."""
    
    def test_import_without_psycopg2(self):
        """Force module reload without psycopg2 to cover lines 86-89."""
        import importlib
        import builtins
        
        # Step 1: Save original psycopg2 if it exists
        psycopg2_backup = sys.modules.get('psycopg2', None)
        psycopg2_extras_backup = sys.modules.get('psycopg2.extras', None)
        
        # Step 2: Remove audit_logger from cache
        modules_to_remove = [
            k for k in list(sys.modules.keys()) 
            if 'audit_logger' in k
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Step 3: Remove psycopg2 from sys.modules to force ImportError
        if 'psycopg2' in sys.modules:
            del sys.modules['psycopg2']
        if 'psycopg2.extras' in sys.modules:
            del sys.modules['psycopg2.extras']
        
        # Step 4: Block psycopg2 import
        real_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'psycopg2' or name.startswith('psycopg2'):
                # Lines 86-89 execute when this ImportError is raised
                raise ImportError(f"No module named '{name}'")
            return real_import(name, *args, **kwargs)
        
        try:
            # Step 5: Patch and import
            builtins.__import__ = mock_import
            
            # Force reimport - lines 86-89 WILL execute
            import backend.shared.audit_logger as audit_module
            
            # Verify lines 86-89 executed
            assert audit_module.POSTGRES_AVAILABLE is False, "Line 88 failed"
            assert audit_module.psycopg2 is None, "Line 89 failed"
            assert audit_module.Json is None, "Line 89 failed"
            
        finally:
            # Step 6: Restore everything
            builtins.__import__ = real_import
            
            # Remove test import
            if 'backend.shared.audit_logger' in sys.modules:
                del sys.modules['backend.shared.audit_logger']
            
            # Restore original psycopg2
            if psycopg2_backup:
                sys.modules['psycopg2'] = psycopg2_backup
            if psycopg2_extras_backup:
                sys.modules['psycopg2.extras'] = psycopg2_extras_backup
            
            # Reimport audit_logger normally for other tests
            import backend.shared.audit_logger
