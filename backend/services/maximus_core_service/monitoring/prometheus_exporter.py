"""
Prometheus Metrics Exporter for MAXIMUS AI 3.0

Exposes comprehensive metrics from all MAXIMUS components:
- Predictive Coding (free energy, latency per layer)
- Neuromodulation (dopamine, ACh, NE, 5-HT levels)
- Skill Learning (executions, success rate, rewards)
- Attention System (salience scores, prioritization)
- Ethical AI (approval rate, rejections)
- System Health (CPU, memory, throughput)

REGRA DE OURO: Zero mocks, production-ready instrumentation
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, Info, generate_latest


class MaximusMetricsExporter:
    """Prometheus metrics exporter for MAXIMUS AI 3.0."""

    def __init__(self, registry: CollectorRegistry | None = None):
        """
        Initialize Prometheus metrics exporter.

        Args:
            registry: Optional CollectorRegistry. If None, creates new registry.
        """
        self.registry = registry or CollectorRegistry()

        # ============================================================
        # PREDICTIVE CODING METRICS (FASE 3)
        # ============================================================
        self.free_energy = Histogram(
            "maximus_free_energy",
            "Free Energy (surprise) by layer - measures prediction error",
            ["layer"],
            registry=self.registry,
            buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
        )

        self.pc_latency = Histogram(
            "maximus_predictive_coding_latency_seconds",
            "Predictive Coding inference latency by layer",
            ["layer"],
            registry=self.registry,
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0],
        )

        self.prediction_errors = Counter(
            "maximus_prediction_errors_total", "Total prediction errors by layer", ["layer"], registry=self.registry
        )

        # ============================================================
        # NEUROMODULATION METRICS (FASE 5)
        # ============================================================
        self.dopamine_level = Gauge(
            "maximus_dopamine_level", "Current dopamine level (RPE - Reward Prediction Error)", registry=self.registry
        )

        self.acetylcholine_level = Gauge(
            "maximus_acetylcholine_level", "Current acetylcholine level (attention modulation)", registry=self.registry
        )

        self.norepinephrine_level = Gauge(
            "maximus_norepinephrine_level", "Current norepinephrine level (arousal/alertness)", registry=self.registry
        )

        self.serotonin_level = Gauge(
            "maximus_serotonin_level", "Current serotonin level (patience/exploration)", registry=self.registry
        )

        self.learning_rate = Gauge(
            "maximus_learning_rate", "Current modulated learning rate (base * dopamine)", registry=self.registry
        )

        # ============================================================
        # SKILL LEARNING METRICS (FASE 6)
        # ============================================================
        self.skill_executions = Counter(
            "maximus_skill_executions_total",
            "Total skill executions by name, mode, and status",
            ["skill_name", "mode", "status"],
            registry=self.registry,
        )

        self.skill_reward = Histogram(
            "maximus_skill_reward",
            "Skill execution rewards distribution",
            ["skill_name"],
            registry=self.registry,
            buckets=[-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0],
        )

        self.skill_latency = Histogram(
            "maximus_skill_execution_latency_seconds",
            "Skill execution latency",
            ["skill_name", "mode"],
            registry=self.registry,
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
        )

        self.skill_success_rate = Gauge(
            "maximus_skill_success_rate", "Skill execution success rate (0-1)", ["skill_name"], registry=self.registry
        )

        # ============================================================
        # ATTENTION SYSTEM METRICS (FASE 0)
        # ============================================================
        self.attention_salience = Histogram(
            "maximus_attention_salience",
            "Event salience scores from attention system",
            registry=self.registry,
            buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
        )

        self.attention_threshold = Gauge(
            "maximus_attention_threshold",
            "Current attention threshold for event prioritization",
            registry=self.registry,
        )

        self.attention_updates = Counter(
            "maximus_attention_updates_total", "Total attention threshold updates", ["reason"], registry=self.registry
        )

        # ============================================================
        # ETHICAL AI METRICS (Ethical AI Stack)
        # ============================================================
        self.ethical_decisions = Counter(
            "maximus_ethical_decisions_total", "Total ethical decisions by result", ["result"], registry=self.registry
        )

        self.ethical_approval_rate = Gauge(
            "maximus_ethical_approval_rate", "Ethical AI approval rate (0-1)", registry=self.registry
        )

        self.ethical_violations = Counter(
            "maximus_ethical_violations_total",
            "Total ethical violations by category",
            ["category"],
            registry=self.registry,
        )

        # ============================================================
        # SYSTEM METRICS
        # ============================================================
        self.events_processed = Counter(
            "maximus_events_processed_total",
            "Total events processed by type and threat status",
            ["event_type", "detected_as_threat"],
            registry=self.registry,
        )

        self.pipeline_latency = Histogram(
            "maximus_pipeline_latency_seconds",
            "End-to-end pipeline latency (event → response)",
            registry=self.registry,
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
        )

        self.threat_detection_accuracy = Gauge(
            "maximus_threat_detection_accuracy", "Current threat detection accuracy (0-1)", registry=self.registry
        )

        self.false_positive_rate = Gauge(
            "maximus_false_positive_rate", "Current false positive rate (0-1)", registry=self.registry
        )

        self.false_negative_rate = Gauge(
            "maximus_false_negative_rate", "Current false negative rate (0-1)", registry=self.registry
        )

        # ============================================================
        # SYSTEM INFO
        # ============================================================
        self.system_info = Info(
            "maximus_system_info", "MAXIMUS AI 3.0 system information and feature flags", registry=self.registry
        )

        # Initialize system info
        self.system_info.info(
            {
                "version": "3.0.0",
                "predictive_coding_enabled": "true",
                "skill_learning_enabled": "true",
                "neuromodulation_enabled": "true",
                "ethical_ai_enabled": "true",
                "regra_de_ouro_compliant": "true",
            }
        )

    # ============================================================
    # PREDICTIVE CODING RECORDING
    # ============================================================
    def record_predictive_coding(self, layer: str, free_energy: float, latency: float):
        """
        Record Predictive Coding metrics for a layer.

        Args:
            layer: Layer name (l1, l2, l3, l4, l5)
            free_energy: Free Energy value (surprise/prediction error)
            latency: Inference latency in seconds
        """
        self.free_energy.labels(layer=layer).observe(free_energy)
        self.pc_latency.labels(layer=layer).observe(latency)
        if free_energy > 0.5:  # Threshold for prediction error
            self.prediction_errors.labels(layer=layer).inc()

    # ============================================================
    # NEUROMODULATION RECORDING
    # ============================================================
    def record_neuromodulation(self, state: dict[str, float]):
        """
        Record Neuromodulation state.

        Args:
            state: Dictionary with neuromodulator levels
                - dopamine: float (RPE signal)
                - acetylcholine: float (attention)
                - norepinephrine: float (arousal)
                - serotonin: float (patience)
                - learning_rate: float (modulated LR)
        """
        if "dopamine" in state:
            self.dopamine_level.set(state["dopamine"])
        if "acetylcholine" in state:
            self.acetylcholine_level.set(state["acetylcholine"])
        if "norepinephrine" in state:
            self.norepinephrine_level.set(state["norepinephrine"])
        if "serotonin" in state:
            self.serotonin_level.set(state["serotonin"])
        if "learning_rate" in state:
            self.learning_rate.set(state["learning_rate"])

    # ============================================================
    # SKILL LEARNING RECORDING
    # ============================================================
    def record_skill_execution(self, skill_name: str, mode: str, success: bool, reward: float, latency: float):
        """
        Record Skill Learning execution metrics.

        Args:
            skill_name: Name of the skill executed
            mode: Execution mode (model_free, model_based, hybrid)
            success: Whether execution was successful
            reward: Reward received (-1 to 1)
            latency: Execution latency in seconds
        """
        status = "success" if success else "failure"
        self.skill_executions.labels(skill_name=skill_name, mode=mode, status=status).inc()
        self.skill_reward.labels(skill_name=skill_name).observe(reward)
        self.skill_latency.labels(skill_name=skill_name, mode=mode).observe(latency)

    def update_skill_success_rate(self, skill_name: str, rate: float):
        """
        Update skill success rate.

        Args:
            skill_name: Name of the skill
            rate: Success rate (0-1)
        """
        self.skill_success_rate.labels(skill_name=skill_name).set(rate)

    # ============================================================
    # ATTENTION SYSTEM RECORDING
    # ============================================================
    def record_attention(self, salience: float, threshold: float):
        """
        Record Attention System metrics.

        Args:
            salience: Event salience score (0-1)
            threshold: Current attention threshold
        """
        self.attention_salience.observe(salience)
        self.attention_threshold.set(threshold)

    def record_attention_update(self, reason: str):
        """
        Record attention threshold update.

        Args:
            reason: Reason for update (high_surprise, low_surprise, manual)
        """
        self.attention_updates.labels(reason=reason).inc()

    # ============================================================
    # ETHICAL AI RECORDING
    # ============================================================
    def record_ethical_decision(self, approved: bool):
        """
        Record Ethical AI decision.

        Args:
            approved: Whether the decision was approved
        """
        result = "approved" if approved else "rejected"
        self.ethical_decisions.labels(result=result).inc()

    def update_ethical_approval_rate(self, rate: float):
        """
        Update Ethical AI approval rate.

        Args:
            rate: Approval rate (0-1)
        """
        self.ethical_approval_rate.set(rate)

    def record_ethical_violation(self, category: str):
        """
        Record ethical violation.

        Args:
            category: Violation category (bias, fairness, privacy, etc.)
        """
        self.ethical_violations.labels(category=category).inc()

    # ============================================================
    # SYSTEM RECORDING
    # ============================================================
    def record_event_processed(self, event_type: str, detected_as_threat: bool, latency: float):
        """
        Record event processing metrics.

        Args:
            event_type: Type of event processed
            detected_as_threat: Whether detected as threat
            latency: Processing latency in seconds
        """
        threat_label = "true" if detected_as_threat else "false"
        self.events_processed.labels(event_type=event_type, detected_as_threat=threat_label).inc()
        self.pipeline_latency.observe(latency)

    def update_detection_metrics(self, accuracy: float, fp_rate: float, fn_rate: float):
        """
        Update threat detection quality metrics.

        Args:
            accuracy: Overall accuracy (0-1)
            fp_rate: False positive rate (0-1)
            fn_rate: False negative rate (0-1)
        """
        self.threat_detection_accuracy.set(accuracy)
        self.false_positive_rate.set(fp_rate)
        self.false_negative_rate.set(fn_rate)

    # ============================================================
    # EXPORT
    # ============================================================
    def get_metrics(self) -> bytes:
        """
        Get Prometheus metrics in text format.

        Returns:
            bytes: Metrics in Prometheus text format
        """
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """
        Get content type for HTTP response.

        Returns:
            str: Content type header value
        """
        return CONTENT_TYPE_LATEST

    def __repr__(self) -> str:
        """String representation."""
        return f"MaximusMetricsExporter(registry={self.registry})"
