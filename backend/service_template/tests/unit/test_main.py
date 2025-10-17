"""
Tests for Main Entry Point

100% coverage required.
"""
from unittest.mock import patch

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

    def test_main_entrypoint(self) -> None:
        """Test __main__ entrypoint."""
        # Coverage for line 30: if __name__ == "__main__"
        # Simpler approach: mock sys.argv and runpy
        import runpy

        with patch("service_template.main.uvicorn.run"):
            with patch("sys.argv", ["service_template.main"]):
                try:
                    runpy.run_module("service_template.main", run_name="__main__")
                except SystemExit:
                    pass  # Expected if uvicorn.run is mocked

        # Line 30 executed
