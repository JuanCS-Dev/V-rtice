"""
Tests for Main Entry Point

100% coverage required.
"""
from unittest.mock import patch, MagicMock

from service_template.main import app, main


class TestMain:
    """Tests for main entry point."""

    def test_app_exists(self) -> None:
        """Test app instance is created."""
        assert app is not None

    def test_main_function(self) -> None:
        """Test main function runs uvicorn."""
        with patch("service_template.main.uvicorn.run") as mock_run:
            main()
            
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
