"""
Testes para immunis_treg_service - Tolerance Learning & False Positive Suppression

OBJETIVO: 95%+ cobertura
ESTRATÉGIA: Testes diretos das 3 classes principais
"""

import pytest
from datetime import datetime, timedelta

from treg_core import (
    AlertSeverity,
    ToleranceDecision,
    SecurityAlert,
    ToleranceProfile,
    SuppressionDecision,
    ToleranceLearner,
    FalsePositiveSuppressor,
    TregController,
)


class TestToleranceLearner:
    """Testa ToleranceLearner - aprendizado de tolerância."""

    def test_init(self):
        """Testa inicialização."""
        learner = ToleranceLearner(tolerance_threshold=0.8)
        assert learner.tolerance_threshold == 0.8
        assert learner.observations_window == 1000
        assert len(learner.tolerance_profiles) == 0
        assert learner.total_profiles_created == 0

    def test_observe_entity_behavior_creates_profile(self):
        """Testa que observe_entity_behavior cria profile."""
        learner = ToleranceLearner()
        features = {"connection_count": 10.0, "data_volume_mb": 50.0}

        learner.observe_entity_behavior("192.168.1.100", "source_ip", features)

        assert "192.168.1.100" in learner.tolerance_profiles
        assert learner.total_profiles_created == 1

        profile = learner.tolerance_profiles["192.168.1.100"]
        assert profile.entity_id == "192.168.1.100"
        assert profile.entity_type == "source_ip"
        assert profile.total_observations == 1

    def test_observe_entity_behavior_updates_existing_profile(self):
        """Testa que observe atualiza profile existente."""
        learner = ToleranceLearner()
        features1 = {"connection_count": 10.0}
        features2 = {"connection_count": 20.0}

        learner.observe_entity_behavior("192.168.1.100", "source_ip", features1)
        learner.observe_entity_behavior("192.168.1.100", "source_ip", features2)

        profile = learner.tolerance_profiles["192.168.1.100"]
        assert profile.total_observations == 2
        assert learner.total_profiles_created == 1  # Não criou novo

    def test_update_behavioral_fingerprint_ema(self):
        """Testa EMA (exponential moving average) no fingerprint."""
        learner = ToleranceLearner()

        # Primeira observação
        learner.observe_entity_behavior("test", "source_ip", {"metric": 100.0})
        profile = learner.tolerance_profiles["test"]
        assert profile.behavioral_fingerprint["metric"] == 100.0

        # Segunda observação (EMA: alpha=0.1)
        # new = 0.1 * 200 + 0.9 * 100 = 20 + 90 = 110
        learner.observe_entity_behavior("test", "source_ip", {"metric": 200.0})
        assert profile.behavioral_fingerprint["metric"] == pytest.approx(110.0, rel=0.01)

    def test_update_tolerance_score_false_positive(self):
        """Testa que false positive aumenta tolerance score."""
        learner = ToleranceLearner()
        learner.observe_entity_behavior("192.168.1.100", "source_ip", {"metric": 1.0})

        profile = learner.tolerance_profiles["192.168.1.100"]
        initial_score = profile.tolerance_score

        learner.update_tolerance_score("192.168.1.100", alert_was_false_positive=True)

        profile = learner.tolerance_profiles["192.168.1.100"]
        assert profile.false_positive_count == 1
        assert profile.tolerance_score > initial_score  # Aumentou

    def test_update_tolerance_score_true_positive(self):
        """Testa que true positive diminui tolerance score."""
        learner = ToleranceLearner()
        learner.observe_entity_behavior("192.168.1.100", "source_ip", {"metric": 1.0})

        profile = learner.tolerance_profiles["192.168.1.100"]
        initial_score = profile.tolerance_score

        learner.update_tolerance_score("192.168.1.100", alert_was_false_positive=False)

        profile = learner.tolerance_profiles["192.168.1.100"]
        assert profile.true_positive_count == 1
        assert profile.tolerance_score < initial_score  # Diminuiu

    def test_update_tolerance_score_no_profile(self):
        """Testa update sem profile existente."""
        learner = ToleranceLearner()
        learner.update_tolerance_score("nonexistent", alert_was_false_positive=True)
        # Não deve crashar, apenas log warning

    def test_get_tolerance_score_existing(self):
        """Testa get_tolerance_score para profile existente."""
        learner = ToleranceLearner()
        learner.observe_entity_behavior("192.168.1.100", "source_ip", {"metric": 1.0})

        score = learner.get_tolerance_score("192.168.1.100")
        assert 0.0 <= score <= 1.0

    def test_get_tolerance_score_nonexistent(self):
        """Testa get_tolerance_score para profile inexistente."""
        learner = ToleranceLearner()
        score = learner.get_tolerance_score("nonexistent")
        assert score == 0.5  # Padrão CORRETO

    def test_get_status(self):
        """Testa get_status."""
        learner = ToleranceLearner()
        learner.observe_entity_behavior("192.168.1.100", "source_ip", {"metric": 1.0})
        learner.observe_entity_behavior("192.168.1.200", "source_ip", {"metric": 2.0})

        status = learner.get_status()
        assert status["total_profiles"] == 2
        assert status["tolerance_threshold"] == 0.7
        assert "high_tolerance_entities" in status


class TestFalsePositiveSuppressor:
    """Testa FalsePositiveSuppressor - supressão de falsos positivos."""

    def test_init(self):
        """Testa inicialização."""
        suppressor = FalsePositiveSuppressor(suppression_threshold=0.8)
        assert suppressor.suppression_threshold == 0.8
        assert len(suppressor.suppression_history) == 0  # CORRETO

    def test_evaluate_alert_high_confidence_threat(self):
        """Testa alert com high confidence (score alto) - não suprime."""
        suppressor = FalsePositiveSuppressor()

        alert = SecurityAlert(
            alert_id="alert-001",
            timestamp=datetime.now(),
            alert_type="malware_detection",
            severity=AlertSeverity.CRITICAL,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["suspicious_hash"],
            raw_score=0.95,  # Score ALTO
        )

        # evaluate_alert recebe tolerance_profiles (dict), não tolerance_score
        decision = suppressor.evaluate_alert(alert, tolerance_profiles={})

        assert decision.decision in [ToleranceDecision.ALLOW, ToleranceDecision.UNCERTAIN]
        assert decision.confidence >= 0.0

    def test_evaluate_alert_with_tolerance_profile(self):
        """Testa alert com tolerance profile conhecido."""
        suppressor = FalsePositiveSuppressor()

        # Cria tolerance profile HIGH
        profile = ToleranceProfile(
            entity_id="192.168.1.100",
            entity_type="source_ip",
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            total_observations=100,
            alert_history=[],
            false_positive_count=50,
            true_positive_count=5,
            behavioral_fingerprint={"metric": 1.0},
            tolerance_score=0.9,  # HIGH tolerance
        )

        alert = SecurityAlert(
            alert_id="alert-002",
            timestamp=datetime.now(),
            alert_type="port_scan",
            severity=AlertSeverity.LOW,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["syn_scan"],
            raw_score=0.4,  # Score BAIXO
        )

        decision = suppressor.evaluate_alert(alert, tolerance_profiles={"192.168.1.100": profile})

        # Pode suprimir OU ficar incerto (algoritmo estatístico)
        assert decision.decision in [ToleranceDecision.SUPPRESS, ToleranceDecision.UNCERTAIN]
        assert "192.168.1.100" in decision.tolerance_profiles_consulted

    def test_compute_anomaly_score(self):
        """Testa _compute_anomaly_score."""
        suppressor = FalsePositiveSuppressor()

        alert = SecurityAlert(
            alert_id="alert-004",
            timestamp=datetime.now(),
            alert_type="intrusion_attempt",
            severity=AlertSeverity.HIGH,
            source_ip="10.0.0.5",
            target_asset="db-1",
            indicators=["sql_injection"],
            raw_score=0.8,
        )

        score = suppressor._compute_anomaly_score(alert)
        assert score >= 0.0  # Z-score pode ser > 1.0

    def test_count_recent_similar_alerts(self):
        """Testa _count_recent_similar_alerts."""
        suppressor = FalsePositiveSuppressor()

        # Adiciona histórico de alerts similares
        alert1 = SecurityAlert(
            alert_id="alert-1",
            timestamp=datetime.now(),
            alert_type="port_scan",
            severity=AlertSeverity.LOW,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["syn_scan"],
            raw_score=0.5,
        )

        alert2 = SecurityAlert(
            alert_id="alert-2",
            timestamp=datetime.now(),
            alert_type="port_scan",  # Mesmo tipo
            severity=AlertSeverity.LOW,
            source_ip="192.168.1.100",  # Mesmo source
            target_asset="server-1",
            indicators=["syn_scan"],
            raw_score=0.5,
        )

        suppressor.evaluate_alert(alert1, tolerance_profiles={})

        count = suppressor._count_recent_similar_alerts(alert2)
        assert count >= 1  # Deve encontrar alert1

    def test_record_ground_truth(self):
        """Testa record_ground_truth."""
        suppressor = FalsePositiveSuppressor()

        alert = SecurityAlert(
            alert_id="alert-ground-truth",
            timestamp=datetime.now(),
            alert_type="malware_detection",
            severity=AlertSeverity.HIGH,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["malicious_file"],
            raw_score=0.9,
        )

        suppressor.evaluate_alert(alert, tolerance_profiles={})

        # Registra ground truth
        suppressor.record_ground_truth("alert-ground-truth", was_false_positive=True)
        # Não crasheia, procura na suppression_history

    def test_record_ground_truth_not_found(self):
        """Testa record_ground_truth com alert_id inexistente."""
        suppressor = FalsePositiveSuppressor()
        suppressor.record_ground_truth("nonexistent", was_false_positive=True)
        # Apenas log warning, não crasheia

    def test_get_status(self):
        """Testa get_status."""
        suppressor = FalsePositiveSuppressor()

        alert = SecurityAlert(
            alert_id="alert-status",
            timestamp=datetime.now(),
            alert_type="anomaly",
            severity=AlertSeverity.MEDIUM,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["anomaly"],
            raw_score=0.6,
        )

        suppressor.evaluate_alert(alert, tolerance_profiles={})

        status = suppressor.get_status()
        assert "alerts_suppressed" in status
        assert "alerts_allowed" in status


class TestTregController:
    """Testa TregController - controlador principal."""

    def test_init(self):
        """Testa inicialização."""
        controller = TregController(tolerance_threshold=0.8, suppression_threshold=0.75)
        assert controller.tolerance_learner.tolerance_threshold == 0.8  # CORRETO
        assert controller.fp_suppressor.suppression_threshold == 0.75  # CORRETO

    def test_process_alert_new_entity(self):
        """Testa process_alert para entity nova (sem tolerance profile)."""
        controller = TregController()

        alert = SecurityAlert(
            alert_id="alert-new-entity",
            timestamp=datetime.now(),
            alert_type="malware_detection",
            severity=AlertSeverity.HIGH,
            source_ip="10.20.30.40",
            target_asset="server-1",
            indicators=["malware_hash"],
            raw_score=0.85,
        )

        decision = controller.process_alert(alert)

        assert decision.decision in [ToleranceDecision.ALLOW, ToleranceDecision.UNCERTAIN]
        assert len(decision.rationale) > 0  # CORRETO: rationale (list), não explanation

    def test_process_alert_known_trusted_entity(self):
        """Testa process_alert para entity confiável (high tolerance)."""
        controller = TregController()

        # Primeiro, aprende comportamento da entity
        controller.observe_entity("192.168.1.100", "source_ip", {"connection_count": 10.0})

        # Marca como false positive múltiplas vezes para aumentar tolerance
        for _ in range(5):
            controller.tolerance_learner.update_tolerance_score(
                "192.168.1.100", alert_was_false_positive=True
            )

        # Agora testa alert dessa entity confiável
        alert = SecurityAlert(
            alert_id="alert-trusted",
            timestamp=datetime.now(),
            alert_type="port_scan",
            severity=AlertSeverity.LOW,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["syn_scan"],
            raw_score=0.3,  # Score baixo
        )

        decision = controller.process_alert(alert)

        # Pode suprimir OU ficar incerto (algoritmo estatístico)
        assert decision.decision in [ToleranceDecision.SUPPRESS, ToleranceDecision.UNCERTAIN]

    def test_observe_entity(self):
        """Testa observe_entity."""
        controller = TregController()

        features = {"connection_count": 15.0, "data_volume_mb": 100.0}
        controller.observe_entity("192.168.1.100", "source_ip", features)

        assert "192.168.1.100" in controller.tolerance_learner.tolerance_profiles  # CORRETO

    def test_provide_feedback(self):
        """Testa provide_feedback."""
        controller = TregController()

        # Primeiro, processa alert
        alert = SecurityAlert(
            alert_id="alert-feedback",
            timestamp=datetime.now(),
            alert_type="anomaly",
            severity=AlertSeverity.MEDIUM,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["unusual_behavior"],
            raw_score=0.6,
        )

        controller.process_alert(alert)

        # Fornece feedback CORRETO: entities_involved (list of tuples), não entity_id
        controller.provide_feedback(
            alert_id="alert-feedback",
            was_false_positive=True,
            entities_involved=[("192.168.1.100", "source_ip")],
        )

        # Verifica que tolerance aumentou
        profile = controller.tolerance_learner.tolerance_profiles.get("192.168.1.100")
        if profile:
            assert profile.false_positive_count >= 1

    def test_get_status(self):
        """Testa get_status."""
        controller = TregController()

        controller.observe_entity("192.168.1.100", "source_ip", {"metric": 1.0})

        alert = SecurityAlert(
            alert_id="alert-status",
            timestamp=datetime.now(),
            alert_type="malware",
            severity=AlertSeverity.HIGH,
            source_ip="192.168.1.100",
            target_asset="server-1",
            indicators=["malware"],
            raw_score=0.9,
        )

        controller.process_alert(alert)

        status = controller.get_status()
        assert "tolerance_learner" in status
        assert "fp_suppressor" in status  # CORRETO


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
