"""
Shared pytest fixtures for MAXIMUS AI 3.0 tests

REGRA DE OURO: Zero mocks, production-ready fixtures
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@pytest.fixture(scope="session")
def torch_available():
    """Check if PyTorch is available."""
    return TORCH_AVAILABLE


@pytest.fixture
def simple_torch_model():
    """Create simple PyTorch model for testing."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")

    class SimpleModel(nn.Module):
        def __init__(self, input_size=128, hidden_size=64, output_size=32):
            super().__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_size, output_size)

        def forward(self, x):
            x = self.fc1(x)
            x = self.relu(x)
            x = self.fc2(x)
            return x

    return SimpleModel()


@pytest.fixture
def sample_threat_data():
    """Sample cybersecurity threat data for testing."""
    return {
        "threat_id": "T001",
        "timestamp": "2025-10-06T12:00:00Z",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.50",
        "port": 443,
        "protocol": "TCP",
        "payload_size": 1024,
        "threat_score": 0.85,
        "threat_type": "malware",
        "indicators": {"suspicious_patterns": 3, "known_malware_signatures": 1, "anomaly_score": 0.72},
    }


@pytest.fixture
def sample_decision_request():
    """Sample decision request for governance/HITL testing."""
    return {
        "decision_id": "DEC001",
        "action": "block_ip",
        "target": "192.168.1.100",
        "risk_level": "HIGH",
        "confidence": 0.89,
        "context": {"threat_score": 0.85, "false_positive_rate": 0.05},
        "ethical_constraints": {"privacy_concern": False, "transparency_required": True},
    }


@pytest.fixture
def sample_model_explanation():
    """Sample XAI explanation for testing."""
    return {
        "prediction": "malicious",
        "confidence": 0.92,
        "feature_importance": {"payload_size": 0.35, "port": 0.28, "suspicious_patterns": 0.22, "anomaly_score": 0.15},
        "counterfactuals": [
            {"feature": "payload_size", "original_value": 1024, "suggested_value": 512, "new_prediction": "benign"}
        ],
    }


@pytest.fixture
def temp_model_path(tmp_path):
    """Temporary path for saving models in tests."""
    return tmp_path / "models"


@pytest.fixture
def temp_data_path(tmp_path):
    """Temporary path for test data."""
    return tmp_path / "data"


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (medium speed, component interaction)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow, full workflow)")
    config.addinivalue_line("markers", "slow: Slow tests (skip with -m 'not slow')")
    config.addinivalue_line("markers", "requires_torch: Tests requiring PyTorch")
    config.addinivalue_line("markers", "requires_gpu: Tests requiring GPU")
