"""
Testes REAIS para immunis_helper_t_service - Helper T-Cell Core

OBJETIVO: 100% COBERTURA ABSOLUTA do helper_t_core.py
- Testa Th1/Th2 strategy selection (biological immune orchestration)
- Testa response intensity modulation
- Testa B-cell and Cytotoxic T-cell coordination
- Testa effectiveness metrics tracking
- ZERO MOCKS desnecessários

Padrão Pagani Absoluto: Helper T-Cell coordena imunidade adaptativa.
"""

import pytest
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_helper_t_service")

from helper_t_core import HelperTCellCore, ImmuneStrategy, ResponseIntensity


class TestImmuneStrategySelection:
    """Testes de seleção de estratégia Th1/Th2."""

    @pytest.mark.asyncio
    async def test_th1_strategy_high_severity(self):
        """Testa que severity >= 0.7 triggera Th1 (agressivo)."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_high_severity",
            "malware_family": "TestMalware",
            "severity": 0.8,  # >= 0.7
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["strategy"] == "th1"
        assert result["coordination"]["cytotoxic_t_activated"] is True  # Th1 ativa Cytotoxic

    @pytest.mark.asyncio
    async def test_th1_strategy_multi_host_campaign(self):
        """Testa que correlation_count >= 5 triggera Th1."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_campaign",
            "malware_family": "Botnet",
            "severity": 0.5,
            "correlation_count": 6,  # >= 5
        }

        result = await core.activate(antigen)

        assert result["strategy"] == "th1"

    @pytest.mark.asyncio
    async def test_th1_strategy_aggressive_malware_family(self):
        """Testa que famílias agressivas (ransomware, worm, rootkit, apt) triggeram Th1."""
        core = HelperTCellCore()

        aggressive_families = ["Ransomware-X", "WormBot", "APT29", "Rootkit-Malicious"]

        for family in aggressive_families:
            antigen = {
                "antigen_id": f"ag_{family}",
                "malware_family": family,
                "severity": 0.4,
                "correlation_count": 0,
            }

            result = await core.activate(antigen)

            assert result["strategy"] == "th1", f"{family} should trigger Th1"

    @pytest.mark.asyncio
    async def test_th2_strategy_isolated_low_severity(self):
        """Testa que ameaça isolada + baixa severity triggera Th2 (defensivo)."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_low_severity",
            "malware_family": "Adware",
            "severity": 0.3,  # < 0.5
            "correlation_count": 0,  # Isolated
        }

        result = await core.activate(antigen)

        assert result["strategy"] == "th2"

    @pytest.mark.asyncio
    async def test_balanced_strategy(self):
        """Testa estratégia BALANCED para casos intermediários."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_medium",
            "malware_family": "Trojan",
            "severity": 0.55,
            "correlation_count": 2,
        }

        result = await core.activate(antigen)

        assert result["strategy"] == "balanced"


class TestResponseIntensity:
    """Testes de cálculo de intensidade de resposta."""

    @pytest.mark.asyncio
    async def test_intensity_critical(self):
        """Testa intensity CRITICAL (score >= 0.8)."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_critical",
            "malware_family": "CriticalThreat",
            "severity": 0.85,
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "critical"

    @pytest.mark.asyncio
    async def test_intensity_high(self):
        """Testa intensity HIGH (0.6 <= score < 0.8)."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_high",
            "malware_family": "HighThreat",
            "severity": 0.65,
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "high"

    @pytest.mark.asyncio
    async def test_intensity_medium(self):
        """Testa intensity MEDIUM (0.4 <= score < 0.6)."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_medium",
            "malware_family": "MediumThreat",
            "severity": 0.5,
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "medium"

    @pytest.mark.asyncio
    async def test_intensity_low(self):
        """Testa intensity LOW (score < 0.4)."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_low",
            "malware_family": "LowThreat",
            "severity": 0.3,
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "low"

    @pytest.mark.asyncio
    async def test_intensity_boost_from_correlation(self):
        """Testa que correlation_count >= 5 adiciona +0.2 ao intensity_score."""
        core = HelperTCellCore()

        # Severity 0.65 + correlation boost 0.2 = 0.85 → CRITICAL
        antigen = {
            "antigen_id": "ag_correlated",
            "malware_family": "Campaign",
            "severity": 0.65,
            "correlation_count": 6,  # >= 5, +0.2 boost
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "critical"  # 0.65 + 0.2 = 0.85

    @pytest.mark.asyncio
    async def test_intensity_boost_from_medium_correlation(self):
        """Testa que 3 <= correlation_count < 5 adiciona +0.1."""
        core = HelperTCellCore()

        # Severity 0.55 + correlation boost 0.1 = 0.65 → HIGH
        antigen = {
            "antigen_id": "ag_correlated_medium",
            "malware_family": "SmallCampaign",
            "severity": 0.55,
            "correlation_count": 4,  # 3-4, +0.1 boost
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "high"  # 0.55 + 0.1 = 0.65


class TestImmuneCoordination:
    """Testes de coordenação B-cell/Cytotoxic T-cell."""

    @pytest.mark.asyncio
    async def test_b_cell_always_activated(self):
        """Testa que B-Cell é SEMPRE ativado (todas estratégias)."""
        core = HelperTCellCore()

        strategies = [
            {"severity": 0.8, "correlation_count": 0},  # Th1
            {"severity": 0.3, "correlation_count": 0},  # Th2
            {"severity": 0.55, "correlation_count": 2},  # Balanced
        ]

        for antigen_data in strategies:
            antigen = {
                "antigen_id": "ag_test",
                "malware_family": "TestFamily",
                **antigen_data,
            }

            result = await core.activate(antigen)

            assert result["coordination"]["b_cell_activated"] is True

    @pytest.mark.asyncio
    async def test_cytotoxic_t_activated_on_th1(self):
        """Testa que Cytotoxic T-Cell é ativado em estratégia Th1."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_th1",
            "malware_family": "Ransomware",
            "severity": 0.75,
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["strategy"] == "th1"
        assert result["coordination"]["cytotoxic_t_activated"] is True

    @pytest.mark.asyncio
    async def test_cytotoxic_t_activated_on_high_intensity(self):
        """Testa que Cytotoxic T-Cell é ativado em HIGH/CRITICAL intensity."""
        core = HelperTCellCore()

        # Th2 strategy mas HIGH intensity
        antigen = {
            "antigen_id": "ag_high_intensity",
            "malware_family": "HighSeverityAdware",
            "severity": 0.65,  # HIGH intensity
            "correlation_count": 0,  # Isolated (Th2)
        }

        result = await core.activate(antigen)

        # Th2 ou balanced, mas intensity=high deve ativar Cytotoxic
        assert result["intensity"] == "high"
        assert result["coordination"]["cytotoxic_t_activated"] is True

    @pytest.mark.asyncio
    async def test_directive_priority_high_for_critical(self):
        """Testa que prioridade é 'high' para intensity CRITICAL."""
        core = HelperTCellCore()

        antigen = {
            "antigen_id": "ag_critical",
            "malware_family": "APT",
            "severity": 0.9,
            "correlation_count": 0,
        }

        result = await core.activate(antigen)

        assert result["intensity"] == "critical"

        # Encontra directive de B-cell
        b_cell_directive = next(d for d in result["coordination"]["directives"] if d["cell_type"] == "b_cell")
        assert b_cell_directive["priority"] == "high"

        # Cytotoxic directive deve ter priority "critical"
        cytotoxic_directive = next(d for d in result["coordination"]["directives"] if d["cell_type"] == "cytotoxic_t")
        assert cytotoxic_directive["priority"] == "critical"


class TestResponseOutcomes:
    """Testes de tracking de outcomes."""

    @pytest.mark.asyncio
    async def test_record_response_outcome(self):
        """Testa gravação de outcome."""
        core = HelperTCellCore()

        outcome = await core.record_response_outcome(
            antigen_id="ag_test", outcome="success", time_to_containment=15.5, false_positive=False
        )

        assert outcome["antigen_id"] == "ag_test"
        assert outcome["outcome"] == "success"
        assert outcome["time_to_containment"] == 15.5
        assert outcome["false_positive"] is False

        # Deve ter armazenado
        assert len(core.response_outcomes) == 1

    @pytest.mark.asyncio
    async def test_record_outcome_without_ttc(self):
        """Testa gravação de outcome sem time_to_containment."""
        core = HelperTCellCore()

        outcome = await core.record_response_outcome(antigen_id="ag_no_ttc", outcome="failure", false_positive=False)

        assert outcome["time_to_containment"] is None


class TestEffectivenessMetrics:
    """Testes de métricas de efetividade."""

    @pytest.mark.asyncio
    async def test_effectiveness_metrics_empty(self):
        """Testa métricas quando não há outcomes."""
        core = HelperTCellCore()

        metrics = await core.get_effectiveness_metrics(time_window_hours=24)

        assert metrics["total_responses"] == 0

    @pytest.mark.asyncio
    async def test_effectiveness_metrics_with_data(self):
        """Testa cálculo de métricas com outcomes reais."""
        core = HelperTCellCore()

        # Grava 10 outcomes: 7 success, 3 failure, 2 FP
        for i in range(7):
            await core.record_response_outcome(f"ag_success_{i}", "success", time_to_containment=10.0 + i)

        for i in range(3):
            await core.record_response_outcome(f"ag_failure_{i}", "failure", time_to_containment=30.0)

        # 2 false positives
        await core.record_response_outcome("ag_fp1", "success", false_positive=True, time_to_containment=5.0)
        await core.record_response_outcome("ag_fp2", "success", false_positive=True, time_to_containment=5.0)

        metrics = await core.get_effectiveness_metrics(time_window_hours=24)

        assert metrics["total_responses"] == 12
        assert metrics["successes"] == 9  # 7 + 2 FPs (outcome=success)
        assert metrics["failures"] == 3
        assert metrics["success_rate"] == 9 / 12  # 0.75
        assert metrics["false_positives"] == 2
        assert metrics["fp_rate"] == 2 / 12  # ~0.167

        # Average TTC
        # 7 success (10-16s) + 3 failure (30s) + 2 FP (5s) = 12 outcomes
        # (10+11+12+13+14+15+16 + 30+30+30 + 5+5) / 12 = 191 / 12 ≈ 15.92
        assert metrics["avg_time_to_containment"] is not None
        assert 15 < metrics["avg_time_to_containment"] < 17

    @pytest.mark.asyncio
    async def test_effectiveness_metrics_filters_by_time_window(self):
        """Testa que métricas filtram por time window."""
        core = HelperTCellCore()

        # Grava outcome recente
        await core.record_response_outcome("ag_recent", "success", time_to_containment=10.0)

        # Simula outcome antigo (manipula timestamp manualmente)
        old_outcome = {
            "timestamp": (datetime.now() - timedelta(hours=48)).isoformat(),
            "antigen_id": "ag_old",
            "outcome": "success",
            "time_to_containment": 20.0,
            "false_positive": False,
        }
        core.response_outcomes.append(old_outcome)

        # Métricas de 24h devem incluir apenas recente
        metrics = await core.get_effectiveness_metrics(time_window_hours=24)

        assert metrics["total_responses"] == 1  # Apenas recente


class TestStatus:
    """Testes do endpoint de status."""

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Testa get_status retorna informações corretas."""
        core = HelperTCellCore()

        # Ativa 3 antigens
        for i in range(3):
            antigen = {
                "antigen_id": f"ag_{i}",
                "malware_family": f"Family{i}",
                "severity": 0.5,
                "correlation_count": 0,
            }
            await core.activate(antigen)

        # Grava 2 outcomes
        await core.record_response_outcome("ag_0", "success")
        await core.record_response_outcome("ag_1", "failure")

        status = await core.get_status()

        assert status["status"] == "operational"
        assert status["threat_intel_count"] == 3
        assert status["directives_issued"] >= 3  # Pelo menos 3 directives (B-cell)
        assert status["outcomes_recorded"] == 2
        assert status["last_coordination"] != "N/A"


class TestIntegration:
    """Testes de integração end-to-end."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Testa ciclo completo: activate → record outcome → metrics."""
        core = HelperTCellCore()

        # 1. Ativa com ransomware (Th1, HIGH)
        antigen = {
            "antigen_id": "ag_ransomware",
            "malware_family": "Ryuk-Ransomware",
            "severity": 0.75,
            "correlation_count": 3,
        }

        activation = await core.activate(antigen)

        assert activation["strategy"] == "th1"
        # 0.75 severity + 0.1 (correlation 3-4) = 0.85 → CRITICAL (>= 0.8)
        assert activation["intensity"] == "critical"
        assert activation["coordination"]["b_cell_activated"] is True
        assert activation["coordination"]["cytotoxic_t_activated"] is True

        # 2. Grava outcome de sucesso
        outcome = await core.record_response_outcome("ag_ransomware", "success", time_to_containment=12.3)

        assert outcome["outcome"] == "success"

        # 3. Verifica métricas
        metrics = await core.get_effectiveness_metrics()

        assert metrics["total_responses"] == 1
        assert metrics["success_rate"] == 1.0

        # 4. Verifica status
        status = await core.get_status()

        assert status["threat_intel_count"] == 1
        assert status["outcomes_recorded"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
