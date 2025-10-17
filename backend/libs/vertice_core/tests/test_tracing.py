"""Tests for vertice_core.tracing module."""


from vertice_core.tracing import setup_tracing


class TestSetupTracing:
    """Tests for setup_tracing function."""

    def test_returns_tracer_when_disabled(self) -> None:
        """Test that tracer is returned when disabled."""
        tracer = setup_tracing(
            service_name="test_service",
            service_version="1.0.0",
            enabled=False,
        )

        assert tracer is not None
        assert hasattr(tracer, "start_span")

    def test_disabled_returns_noop_tracer(self) -> None:
        """Test that disabled tracing returns a NoOp tracer."""
        tracer = setup_tracing(
            service_name="test_noop",
            service_version="1.0.0",
            enabled=False,
        )

        # NoOp tracer should allow span creation without side effects
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None
            span.set_attribute("test", "value")  # Should not raise
