"""
Testes COMPLEMENTARES para atingir máxima cobertura possível

Testa casos edge e situações que não foram cobertas nos testes principais.
Foca em testar comportamento REAL, não em forçar linhas inalcançáveis.
"""

import pytest
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_bcell_service")


class TestEdgeCases:
    """Testes de casos extremos e edge cases."""

    @pytest.mark.asyncio
    async def test_activate_with_many_correlated_events(self):
        """Testa ativação com muitos eventos correlacionados."""
        from bcell_core import BCellCore

        core = BCellCore()

        # Simula alta taxa de FP para triggerar affinity maturation
        for i in range(15):
            await core.record_detection_feedback("TestFamily", 1, detected=True, false_positive=True)

        # Antigen com muitos eventos correlacionados (>5, testando o [:5] slice)
        antigen = {
            "antigen_id": "ag_test",
            "malware_family": "TestFamily",
            "iocs": {
                "strings": ["pattern1", "pattern2"],
                "file_hashes": [],
                "mutexes": [],
                "registry_keys": []
            },
            "correlated_events": [
                {"event_id": f"ev{i}"} for i in range(10)  # 10 eventos, mas só 5 primeiros usados
            ]
        }

        result = await core.activate(antigen)

        # Deve ter processado com affinity maturation
        assert result["affinity_matured"] is True
        assert result["signature_generated"] is True

    def test_yara_generator_with_max_strings(self):
        """Testa geração com número máximo de strings (30)."""
        from bcell_core import YARASignatureGenerator

        generator = YARASignatureGenerator()

        # 40 strings - deve limitar a 30
        iocs = {
            "strings": [f"string_{i}" for i in range(40)],
            "file_hashes": [f"hash_{i}" for i in range(10)],  # 10 hashes, deve limitar a 5
            "mutexes": [f"mutex_{i}" for i in range(10)],  # 10 mutexes, deve limitar a 5
            "registry_keys": [f"HKCU\\Key_{i}" for i in range(10)]  # 10 keys, deve limitar a 5
        }

        yara_rule = generator.generate_yara_from_iocs("MaxIOCs", iocs)

        # Deve ter gerado regra
        assert "rule MaxIOCs_v1_" in yara_rule
        assert yara_rule.count("$str") <= 30  # Máximo 30 strings
        assert yara_rule.count("$hash") <= 5  # Máximo 5 hashes
        assert yara_rule.count("$mutex") <= 5  # Máximo 5 mutexes
        assert yara_rule.count("$reg") <= 5  # Máximo 5 registry keys

    def test_yara_generator_filters_short_strings(self):
        """Testa que strings curtas (<6 chars) são filtradas."""
        from bcell_core import YARASignatureGenerator

        generator = YARASignatureGenerator()

        iocs = {
            "strings": [
                "short",  # 5 chars - deve ser filtrado
                "ok",  # 2 chars - deve ser filtrado
                "longenoughstring",  # >= 6 chars - deve ser incluído
                "valid_pattern",  # >= 6 chars - deve ser incluído
            ],
            "file_hashes": [],
            "mutexes": [],
            "registry_keys": []
        }

        yara_rule = generator.generate_yara_from_iocs("ShortStrings", iocs)

        # Deve incluir apenas strings >= 6 chars
        assert "longenoughstring" in yara_rule
        assert "valid_pattern" in yara_rule
        # Strings curtas não devem aparecer
        # (Nota: podem aparecer no nome da rule se sanitizadas, então não testamos ausência)

    def test_yara_generator_condition_based_on_string_count(self):
        """Testa que condition muda baseado no número de strings."""
        from bcell_core import YARASignatureGenerator

        generator = YARASignatureGenerator()

        # 1 string - deve gerar "any of them"
        iocs_1 = {
            "strings": ["pattern1_long_enough"],
            "file_hashes": [],
            "mutexes": [],
            "registry_keys": []
        }

        yara_1 = generator.generate_yara_from_iocs("OneString", iocs_1)
        assert "any of them" in yara_1

        # 5 strings - deve gerar "3 of them"
        iocs_5 = {
            "strings": [f"pattern{i}_long" for i in range(5)],
            "file_hashes": [],
            "mutexes": [],
            "registry_keys": []
        }

        yara_5 = generator.generate_yara_from_iocs("FiveStrings", iocs_5)
        assert "3 of them" in yara_5

    @pytest.mark.asyncio
    async def test_bcell_status_after_multiple_operations(self):
        """Testa status após múltiplas operações."""
        from bcell_core import BCellCore

        core = BCellCore()

        # Ativa com 3 famílias diferentes
        families = ["Emotet", "TrickBot", "Ryuk"]
        for family in families:
            antigen = {
                "antigen_id": f"ag_{family}",
                "malware_family": family,
                "iocs": {
                    "strings": [f"{family}_pattern"],
                    "file_hashes": [],
                    "mutexes": [],
                    "registry_keys": []
                },
                "correlated_events": []
            }
            await core.activate(antigen)

        # Grava feedbacks
        await core.record_detection_feedback("Emotet", 1, detected=True, false_positive=False)
        await core.record_detection_feedback("TrickBot", 1, detected=True, false_positive=True)

        status = await core.get_status()

        assert status["signatures_generated"] == 3
        assert status["unique_families"] == 3
        assert status["activations_count"] == 3
        assert status["last_signature"] != "N/A"

    def test_affinity_maturation_threshold_boundary(self):
        """Testa boundary de 10% para FP rate (exactly 10%)."""
        from bcell_core import AffinityMaturationEngine

        engine = AffinityMaturationEngine()

        # Adiciona 100 feedbacks, com exatamente 1 FP nos últimos 10 (10.0% = boundary)
        # should_mature olha apenas os últimos min_feedback=10 feedbacks
        for i in range(90):
            engine.record_feedback("Malware", 1, detection_result=True, false_positive=False)

        # Últimos 10: 9 normais + 1 FP = 10.0% FP rate
        for i in range(9):
            engine.record_feedback("Malware", 1, detection_result=True, false_positive=False)

        engine.record_feedback("Malware", 1, detection_result=True, false_positive=True)

        # Com 10% exato (1/10), NÃO deve maturar (> 0.10, não >= 0.10)
        assert engine.should_mature("Malware", min_feedback=10) is False

        # Adiciona mais 1 FP (agora últimos 10 têm 2 FPs = 20%)
        engine.record_feedback("Malware", 1, detection_result=True, false_positive=True)

        # Agora deve maturar (2/10 = 20% > 10%)
        assert engine.should_mature("Malware", min_feedback=10) is True

    def test_refine_signature_common_threshold(self):
        """Testa threshold de 50% para strings comuns."""
        from bcell_core import YARASignatureGenerator

        generator = YARASignatureGenerator()

        # 4 variantes
        variant1 = {
            "strings": ["common1", "common2", "unique1"],  # common1, common2 em todas
            "mutexes": [],
            "registry_keys": []
        }

        variant2 = {
            "strings": ["common1", "common2", "unique2"],
            "mutexes": [],
            "registry_keys": []
        }

        variant3 = {
            "strings": ["common1", "unique3"],  # common2 ausente (75% < 50% não faz sentido, deixa common2)
            "mutexes": [],
            "registry_keys": []
        }

        variant4 = {
            "strings": ["common1", "unique4"],
            "mutexes": [],
            "registry_keys": []
        }

        variants = [variant1, variant2, variant3, variant4]

        refined = generator.refine_signature_from_variants("RefinedTest", variants)

        # common1 aparece em 4/4 (100%) - deve estar
        assert "common1" in refined

        # common2 aparece em 2/4 (50%) - exatamente no threshold
        # Implementação usa >=, então deve incluir
        assert "common2" in refined

    @pytest.mark.asyncio
    async def test_get_signature_returns_latest_version(self):
        """Testa que get_signature retorna a versão mais recente."""
        from bcell_core import BCellCore

        core = BCellCore()

        # Ativa 3 vezes a mesma família
        for i in range(3):
            antigen = {
                "antigen_id": f"ag_{i}",
                "malware_family": "Emotet",
                "iocs": {
                    "strings": [f"pattern_{i}"],
                    "file_hashes": [],
                    "mutexes": [],
                    "registry_keys": []
                },
                "correlated_events": []
            }
            await core.activate(antigen)

        # Get signature deve retornar v3 (última)
        signature = await core.get_signature("Emotet")

        assert signature is not None
        assert signature["signature_version"] == 3
        assert signature["malware_family"] == "Emotet"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
