"""
Testes de exception handling para immunis_treg_service API

OBJETIVO: Cobrir exception handlers (lines 227-229, 267-269, 321-323, 363-365, 403-405, 436-438)
ESTRATÉGIA: Mockar métodos do treg_controller APÓS lifespan inicializar
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from datetime import datetime
import api
from api import app


class TestAPIExceptionHandlers:
    """Testa exception handlers na API."""

    def test_observe_entity_exception_handler(self):
        """Testa exception handler em /tolerance/observe (lines 227-229)."""
        with TestClient(app) as client:
            # Salva método original
            original_method = api.treg_controller.observe_entity

            try:
                # Mock para lançar exception
                api.treg_controller.observe_entity = MagicMock(
                    side_effect=RuntimeError("Database error")
                )

                observation_request = {
                    "entity_id": "test-exception",
                    "entity_type": "source_ip",
                    "behavioral_features": {"metric": 1.0},
                }

                response = client.post("/tolerance/observe", json=observation_request)

                # Deve retornar 500 com exception handler (lines 227-229)
                assert response.status_code == 500
                assert "Database error" in response.json()["detail"]

            finally:
                # Restaura método original
                api.treg_controller.observe_entity = original_method

    def test_get_tolerance_profile_general_exception(self):
        """Testa exception handler geral em get_tolerance_profile (lines 267-269)."""
        with TestClient(app) as client:
            # Salva atributo original
            original_profiles = api.treg_controller.tolerance_learner.tolerance_profiles

            try:
                # Mock para lançar exception no __contains__
                mock_dict = MagicMock()
                mock_dict.__contains__.side_effect = RuntimeError("Internal error")
                api.treg_controller.tolerance_learner.tolerance_profiles = mock_dict

                response = client.get("/tolerance/profile/test")

                # Deve retornar 500 (lines 267-269)
                assert response.status_code == 500
                assert "Internal error" in response.json()["detail"]

            finally:
                # Restaura atributo original
                api.treg_controller.tolerance_learner.tolerance_profiles = original_profiles

    def test_list_tolerance_profiles_with_filters_coverage(self):
        """Testa list_tolerance_profiles com limit e filtros para cobrir lines 297, 299."""
        with TestClient(app) as client:
            # Cria profiles
            for i in range(10):
                observation_request = {
                    "entity_id": f"filter-test-{i}",
                    "entity_type": "source_ip" if i % 2 == 0 else "user",
                    "behavioral_features": {"metric": float(i) * 0.05},
                }
                client.post("/tolerance/observe", json=observation_request)

            # Testa limit (line 297)
            response = client.get("/tolerance/profiles?limit=5")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 5

            # Testa entity_type (line 299)
            response = client.get("/tolerance/profiles?entity_type=user")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_list_tolerance_profiles_exception_via_corrupt_data(self):
        """Testa exception handler lines 321-323 via dados corrompidos."""
        with TestClient(app) as client:
            # Salva profiles original
            original_profiles = api.treg_controller.tolerance_learner.tolerance_profiles

            try:
                # Cria dict com profile corrompido que vai crashear no isoformat()
                corrupt_profile = MagicMock()
                corrupt_profile.entity_id = "corrupt"
                corrupt_profile.entity_type = "test"
                corrupt_profile.first_seen.isoformat.side_effect = RuntimeError("Date error")

                # Injeta profile corrompido
                api.treg_controller.tolerance_learner.tolerance_profiles = {"corrupt": corrupt_profile}

                response = client.get("/tolerance/profiles")

                # Deve retornar 500 (lines 321-323)
                assert response.status_code == 500

            finally:
                # Restaura
                api.treg_controller.tolerance_learner.tolerance_profiles = original_profiles

    def test_provide_feedback_exception_handler(self):
        """Testa exception handler em provide_feedback (lines 363-365)."""
        with TestClient(app) as client:
            # Salva método original
            original_method = api.treg_controller.fp_suppressor.record_ground_truth

            try:
                # Mock para lançar exception
                api.treg_controller.fp_suppressor.record_ground_truth = MagicMock(
                    side_effect=RuntimeError("Feedback error")
                )

                feedback_request = {
                    "alert_id": "test-feedback-exception",
                    "was_false_positive": True,
                    "entities_involved": [{"entity_id": "test", "entity_type": "source_ip"}],
                }

                response = client.post("/feedback/provide", json=feedback_request)

                # Deve retornar 500 (lines 363-365)
                assert response.status_code == 500
                assert "Feedback error" in response.json()["detail"]

            finally:
                # Restaura
                api.treg_controller.fp_suppressor.record_ground_truth = original_method

    def test_get_status_exception_handler(self):
        """Testa exception handler em get_status (lines 403-405)."""
        with TestClient(app) as client:
            # Salva método original
            original_method = api.treg_controller.get_status

            try:
                # Mock para lançar exception
                api.treg_controller.get_status = MagicMock(side_effect=RuntimeError("Status error"))

                response = client.get("/status")

                # Deve retornar 500 (lines 403-405)
                assert response.status_code == 500
                assert "Status error" in response.json()["detail"]

            finally:
                # Restaura
                api.treg_controller.get_status = original_method

    def test_get_statistics_exception_handler(self):
        """Testa exception handler em get_statistics (lines 436-438)."""
        with TestClient(app) as client:
            # Salva método original
            original_method = api.treg_controller.get_status

            try:
                # Mock para lançar exception
                api.treg_controller.get_status = MagicMock(
                    side_effect=RuntimeError("Statistics error")
                )

                response = client.get("/stats")

                # Deve retornar 500 (lines 436-438)
                assert response.status_code == 500
                assert "Statistics error" in response.json()["detail"]

            finally:
                # Restaura
                api.treg_controller.get_status = original_method


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
