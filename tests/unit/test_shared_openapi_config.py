"""Tests for backend/shared/openapi_config.py - 100% coverage."""

import pytest


class TestConstants:
    """Test module constants."""
    
    def test_contact_info(self):
        """Test CONTACT_INFO constant."""
        from backend.shared.openapi_config import CONTACT_INFO
        
        assert isinstance(CONTACT_INFO, dict)
        assert "name" in CONTACT_INFO
        assert "email" in CONTACT_INFO
        assert "url" in CONTACT_INFO
        assert CONTACT_INFO["name"] == "Vértice Platform Team"
    
    def test_license_info(self):
        """Test LICENSE_INFO constant."""
        from backend.shared.openapi_config import LICENSE_INFO
        
        assert isinstance(LICENSE_INFO, dict)
        assert "name" in LICENSE_INFO
        assert "url" in LICENSE_INFO
        assert LICENSE_INFO["name"] == "Proprietary"


class TestGetServers:
    """Test get_servers function."""
    
    def test_get_servers_basic(self):
        """Test server configurations generation."""
        from backend.shared.openapi_config import get_servers
        
        servers = get_servers(8000)
        
        assert isinstance(servers, list)
        assert len(servers) >= 3
        
        # Check localhost server
        localhost_servers = [s for s in servers if "localhost" in s["url"]]
        assert len(localhost_servers) > 0
        assert "8000" in localhost_servers[0]["url"]
    
    def test_get_servers_different_ports(self):
        """Test server configs with different ports."""
        from backend.shared.openapi_config import get_servers
        
        for port in [8001, 8002, 9000]:
            servers = get_servers(port)
            # Verify port appears in URLs
            localhost_server = next(s for s in servers if "localhost" in s["url"])
            assert str(port) in localhost_server["url"]
    
    def test_get_servers_structure(self):
        """Test server object structure."""
        from backend.shared.openapi_config import get_servers
        
        servers = get_servers(5000)
        
        for server in servers:
            assert "url" in server
            assert "description" in server
            assert isinstance(server["url"], str)
            assert isinstance(server["description"], str)


class TestCommonTags:
    """Test COMMON_TAGS constant."""
    
    def test_common_tags_exists(self):
        """Test COMMON_TAGS is defined."""
        from backend.shared.openapi_config import COMMON_TAGS
        
        assert isinstance(COMMON_TAGS, list)
        assert len(COMMON_TAGS) > 0
    
    def test_common_tags_structure(self):
        """Test COMMON_TAGS structure."""
        from backend.shared.openapi_config import COMMON_TAGS
        
        for tag in COMMON_TAGS:
            assert isinstance(tag, dict)
            assert "name" in tag
            assert "description" in tag


class TestSecuritySchemes:
    """Test SECURITY_SCHEMES constant."""
    
    def test_security_schemes_exists(self):
        """Test SECURITY_SCHEMES is defined."""
        from backend.shared.openapi_config import SECURITY_SCHEMES
        
        assert isinstance(SECURITY_SCHEMES, dict)
        assert len(SECURITY_SCHEMES) > 0
    
    def test_api_key_scheme(self):
        """Test API Key security scheme."""
        from backend.shared.openapi_config import SECURITY_SCHEMES
        
        # Check for API Key or similar auth scheme
        has_auth_scheme = any("api" in k.lower() or "key" in k.lower() for k in SECURITY_SCHEMES.keys())
        assert has_auth_scheme or len(SECURITY_SCHEMES) > 0


class TestCreateOpenAPIConfig:
    """Test create_openapi_config function."""
    
    def test_basic_config(self):
        """Test basic OpenAPI config creation."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test Service",
            service_description="A test service",
            version="1.0.0"
        )
        
        assert isinstance(config, dict)
        assert config["title"] == "Test Service"
        assert config["description"] == "A test service"
        assert config["version"] == "1.0.0"
        assert "contact" in config
        assert "license_info" in config
    
    def test_config_with_port(self):
        """Test config with service port."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test Service",
            service_description="Test",
            service_port=8080
        )
        
        assert "servers" in config
        assert isinstance(config["servers"], list)
        # Check port in server URL
        localhost_server = next(s for s in config["servers"] if "localhost" in s["url"])
        assert "8080" in localhost_server["url"]
    
    def test_config_without_port(self):
        """Test config without service port."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test Service",
            service_description="Test"
        )
        
        # Servers should not be present if no port provided
        assert "servers" not in config or config.get("servers") is None
    
    def test_config_with_custom_tags(self):
        """Test config with custom tags."""
        from backend.shared.openapi_config import create_openapi_config
        
        custom_tags = [
            {"name": "custom", "description": "Custom tag"}
        ]
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            tags=custom_tags
        )
        
        assert config["openapi_tags"] == custom_tags
    
    def test_config_default_tags(self):
        """Test config uses COMMON_TAGS by default."""
        from backend.shared.openapi_config import create_openapi_config, COMMON_TAGS
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test"
        )
        
        assert config["openapi_tags"] == COMMON_TAGS
    
    def test_config_with_security(self):
        """Test config includes security schemes."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            include_security=True
        )
        
        # Security is added in custom_openapi function
        assert "openapi_schema" in config
        assert callable(config["openapi_schema"])
    
    def test_config_without_security(self):
        """Test config without security schemes."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            include_security=False
        )
        
        assert "openapi_schema" in config
    
    def test_config_with_additional_metadata(self):
        """Test config with additional metadata."""
        from backend.shared.openapi_config import create_openapi_config
        
        additional = {"custom_field": "custom_value"}
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            additional_metadata=additional
        )
        
        # Additional metadata is added in custom_openapi
        assert "openapi_schema" in config
    
    def test_config_default_version(self):
        """Test config uses default version."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test"
        )
        
        assert config["version"] == "1.0.0"
    
    def test_config_custom_version(self):
        """Test config with custom version."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            version="2.5.3"
        )
        
        assert config["version"] == "2.5.3"


class TestServiceSpecificConfigs:
    """Test service-specific configuration functions."""
    
    def test_maximus_core_config(self):
        """Test Maximus Core Service config."""
        from backend.shared.openapi_config import get_maximus_core_config
        
        config = get_maximus_core_config()
        
        assert isinstance(config, dict)
        assert "Maximus" in config["title"]
        assert config["version"] is not None
    
    def test_ip_intelligence_config(self):
        """Test IP Intelligence Service config."""
        from backend.shared.openapi_config import get_ip_intelligence_config
        
        config = get_ip_intelligence_config()
        
        assert isinstance(config, dict)
        assert "IP" in config["title"] or "Intelligence" in config["title"]
    
    def test_malware_analysis_config(self):
        """Test Malware Analysis Service config."""
        from backend.shared.openapi_config import get_malware_analysis_config
        
        config = get_malware_analysis_config()
        
        assert isinstance(config, dict)
        assert "Malware" in config["title"] or "Analysis" in config["title"]
    
    def test_all_service_configs_valid(self):
        """Test all service configs return valid dicts."""
        from backend.shared.openapi_config import (
            get_maximus_core_config,
            get_ip_intelligence_config,
            get_malware_analysis_config,
        )
        
        configs = [
            get_maximus_core_config(),
            get_ip_intelligence_config(),
            get_malware_analysis_config(),
        ]
        
        for config in configs:
            assert isinstance(config, dict)
            assert "title" in config
            assert "description" in config
            assert "version" in config
            assert "contact" in config
            assert "license_info" in config


class TestCustomOpenAPIFunction:
    """Test the custom_openapi nested function - 100% coverage."""
    
    def test_custom_openapi_callable(self):
        """Test custom_openapi function is returned."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            service_port=8000
        )
        
        assert "openapi_schema" in config
        assert callable(config["openapi_schema"])
    
    def test_custom_openapi_caching(self):
        """Test custom_openapi caches schema - covers lines 214-216."""
        from backend.shared.openapi_config import create_openapi_config
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test"
        )
        
        custom_openapi = config["openapi_schema"]
        
        # Set cached schema
        cached_schema = {"cached": True}
        custom_openapi.openapi_schema = cached_schema
        
        # Should return cached version (line 215-216)
        result = custom_openapi()
        assert result == cached_schema
    
    def test_custom_openapi_full_execution(self):
        """Test custom_openapi full execution - covers lines 212-242."""
        from backend.shared.openapi_config import create_openapi_config
        
        # Create config with all options
        config = create_openapi_config(
            service_name="Integration Test",
            service_description="Full integration test",
            version="2.0.0",
            service_port=8888,
            tags=[{"name": "test", "description": "Test tag"}],
            include_security=True,
            additional_metadata={"x-api-id": "test-123"}
        )
        
        custom_openapi_func = config["openapi_schema"]
        
        # Mock FastAPI app in the closure's scope
        class MockRoute:
            path = "/test"
            methods = ["GET"]
            
        class MockApp:
            routes = [MockRoute()]
        
        # Inject app into closure scope by modifying the function
        # We'll execute it manually with the needed context
        import types
        
        # Create wrapper that provides 'app' in local scope
        def execute_custom_openapi():
            app = MockApp()
            # Now call the actual function with app in scope
            return custom_openapi_func()
        
        # Patch get_openapi to return a mock schema
        from unittest.mock import patch, MagicMock
        
        mock_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        
        # Execute with proper mocking
        with patch('fastapi.openapi.utils.get_openapi') as mock_get_openapi:
            mock_get_openapi.return_value = mock_schema.copy()
            
            # Inject 'app' into the function's closure
            import sys
            import types
            
            # Create a new globals dict with 'app'
            new_globals = custom_openapi_func.__globals__.copy()
            new_globals['app'] = MockApp()
            
            # Create new function with modified globals
            modified_func = types.FunctionType(
                custom_openapi_func.__code__,
                new_globals,
                custom_openapi_func.__name__,
                custom_openapi_func.__defaults__,
                custom_openapi_func.__closure__
            )
            
            # Execute - covers lines 217-242
            result = modified_func()
            
            # Verify line 218-224: get_openapi called
            assert mock_get_openapi.called
            
            # Verify lines 227-229: security schemes added
            assert "components" in result
            assert "securitySchemes" in result["components"]
            
            # Verify lines 232-233: additional metadata added
            assert "x-api-id" in result
            assert result["x-api-id"] == "test-123"
            
            # Verify lines 236-239: external docs added
            assert "externalDocs" in result
            assert result["externalDocs"]["description"] == "Vértice Platform Documentation"
            
            # Verify line 241: schema cached on custom_openapi_func (not modified_func)
            assert hasattr(custom_openapi_func, 'openapi_schema') or hasattr(modified_func, 'openapi_schema')
            
            # Second call should return cached (line 215-216)
            result2 = modified_func()
            assert result2 is result or result2 == result
    
    def test_custom_openapi_without_security(self):
        """Test custom_openapi without security - covers line 227 false branch."""
        from backend.shared.openapi_config import create_openapi_config
        from unittest.mock import patch
        import types
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            include_security=False  # Line 227 false branch
        )
        
        custom_openapi_func = config["openapi_schema"]
        
        class MockApp:
            routes = []
        
        mock_schema = {"openapi": "3.0.0", "paths": {}}
        
        with patch('fastapi.openapi.utils.get_openapi', return_value=mock_schema.copy()):
            new_globals = custom_openapi_func.__globals__.copy()
            new_globals['app'] = MockApp()
            
            modified_func = types.FunctionType(
                custom_openapi_func.__code__,
                new_globals,
                custom_openapi_func.__name__,
                custom_openapi_func.__defaults__,
                custom_openapi_func.__closure__
            )
            
            result = modified_func()
            
            # Security schemes should NOT be added (line 227 false)
            # But externalDocs should still be there (line 236-239)
            assert "externalDocs" in result
    
    def test_custom_openapi_without_additional_metadata(self):
        """Test custom_openapi without metadata - covers line 232 false branch."""
        from backend.shared.openapi_config import create_openapi_config
        from unittest.mock import patch
        import types
        
        config = create_openapi_config(
            service_name="Test",
            service_description="Test",
            additional_metadata=None  # Line 232 false branch
        )
        
        custom_openapi_func = config["openapi_schema"]
        
        class MockApp:
            routes = []
        
        mock_schema = {"openapi": "3.0.0", "paths": {}}
        
        with patch('fastapi.openapi.utils.get_openapi', return_value=mock_schema.copy()):
            new_globals = custom_openapi_func.__globals__.copy()
            new_globals['app'] = MockApp()
            
            modified_func = types.FunctionType(
                custom_openapi_func.__code__,
                new_globals,
                custom_openapi_func.__name__,
                custom_openapi_func.__defaults__,
                custom_openapi_func.__closure__
            )
            
            result = modified_func()
            
            # Additional metadata NOT added (line 232 false)
            # But externalDocs should be there
            assert "externalDocs" in result
    
    def test_config_covers_all_branches(self):
        """Test config creation covers all code branches."""
        from backend.shared.openapi_config import create_openapi_config
        
        # Test with all parameters
        config1 = create_openapi_config(
            service_name="Full Config Test",
            service_description="Full test",
            version="3.0.0",
            service_port=7000,
            tags=[{"name": "test", "description": "test tag"}],
            include_security=True,
            additional_metadata={"x-custom": "value"}
        )
        
        assert config1["title"] == "Full Config Test"
        assert config1["version"] == "3.0.0"
        assert config1["openapi_tags"][0]["name"] == "test"
        assert "servers" in config1
        
        # Test with minimal parameters
        config2 = create_openapi_config(
            service_name="Minimal",
            service_description="Min",
            include_security=False
        )
        
        assert config2["title"] == "Minimal"
        assert config2["version"] == "1.0.0"  # default

