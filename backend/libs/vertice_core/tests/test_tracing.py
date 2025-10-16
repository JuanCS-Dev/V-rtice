"""Tests for vertice_core.tracing module."""

from vertice_core.tracing import setup_tracing


class TestSetupTracing:
    """Tests for setup_tracing function."""

    def test_returns_tracer_when_disabled(self) -> None:
        """Test that tracer is returned when disabled."""
        tracer = setup_tracing(
            service_name="test",
            service_version="1.0.0",
            enabled=False,
        )

        assert tracer is not None
        assert hasattr(tracer, "start_span")
