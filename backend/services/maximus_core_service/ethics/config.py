"""Configuration for ethical frameworks.

This module provides default configurations for all ethical frameworks
and the integration engine.
"""

from typing import Any, Dict

# Default configuration for Ethical Integration Engine
DEFAULT_INTEGRATION_CONFIG: Dict[str, Any] = {
    # Framework weights (must sum to 1.0)
    "framework_weights": {
        "kantian_deontology": 0.30,  # Highest weight due to veto power
        "consequentialism": 0.25,
        "virtue_ethics": 0.20,
        "principialism": 0.25,
    },
    # Veto settings
    "veto_frameworks": ["kantian_deontology"],  # Only Kantian has veto
    "veto_enabled": True,
    # Decision thresholds
    "approval_threshold": 0.70,  # >= 0.70 = APPROVED
    "rejection_threshold": 0.40,  # < 0.40 = REJECTED
    # Between 0.40 and 0.70 = ESCALATED_HITL (if disagreement)
    # HITL escalation
    "hitl_escalation_enabled": True,
    "hitl_disagreement_threshold": 0.75,  # < 75% agreement triggers HITL
    # Cache settings
    "cache_size": 10000,
    "cache_ttl": 3600,  # 1 hour
    # Framework-specific configs
    "kantian": {"veto_enabled": True, "strict_mode": True, "version": "1.0.0"},
    "consequentialist": {
        "weights": {
            "intensity": 0.20,
            "duration": 0.15,
            "certainty": 0.25,
            "propinquity": 0.10,
            "fecundity": 0.15,
            "purity": 0.10,
            "extent": 0.05,
        },
        "approval_threshold": 0.60,
    },
    "virtue": {
        "virtue_weights": {
            "courage": 0.20,
            "temperance": 0.20,
            "justice": 0.20,
            "wisdom": 0.25,
            "honesty": 0.10,
            "vigilance": 0.05,
        },
        "approval_threshold": 0.70,
    },
    "principialism": {
        "weights": {
            "beneficence": 0.25,
            "non_maleficence": 0.35,  # "First, do no harm"
            "autonomy": 0.20,
            "justice": 0.20,
        },
        "approval_threshold": 0.65,
    },
}


# Production configuration (stricter)
PRODUCTION_CONFIG: Dict[str, Any] = {
    **DEFAULT_INTEGRATION_CONFIG,
    # Stricter thresholds in production
    "approval_threshold": 0.75,
    "rejection_threshold": 0.35,
    # Always enable veto in production
    "veto_enabled": True,
    # Framework-specific production configs
    "kantian": {"veto_enabled": True, "strict_mode": True, "version": "1.0.0"},
    "consequentialist": {
        **DEFAULT_INTEGRATION_CONFIG["consequentialist"],
        "approval_threshold": 0.65,  # Stricter
    },
    "virtue": {
        **DEFAULT_INTEGRATION_CONFIG["virtue"],
        "approval_threshold": 0.75,  # Stricter
    },
    "principialism": {
        **DEFAULT_INTEGRATION_CONFIG["principialism"],
        "approval_threshold": 0.70,  # Stricter
    },
}


# Development/testing configuration (more permissive)
DEV_CONFIG: Dict[str, Any] = {
    **DEFAULT_INTEGRATION_CONFIG,
    # More permissive in dev
    "approval_threshold": 0.60,
    "rejection_threshold": 0.45,
    # Disable veto in dev (for testing)
    "veto_enabled": False,
    "kantian": {"veto_enabled": False, "strict_mode": False, "version": "1.0.0"},
}


# Red team / offensive operations configuration
OFFENSIVE_CONFIG: Dict[str, Any] = {
    **DEFAULT_INTEGRATION_CONFIG,
    # Much stricter for offensive ops
    "approval_threshold": 0.85,
    "rejection_threshold": 0.30,
    # Kantian veto is critical for offensive
    "veto_enabled": True,
    # Increase Kantian weight for offensive
    "framework_weights": {
        "kantian_deontology": 0.40,
        "consequentialism": 0.25,
        "virtue_ethics": 0.15,
        "principialism": 0.20,
    },
    # Always escalate to HITL for offensive operations
    "hitl_escalation_enabled": True,
    "hitl_disagreement_threshold": 0.90,  # Even slight disagreement triggers HITL
    "kantian": {"veto_enabled": True, "strict_mode": True, "version": "1.0.0"},
    "consequentialist": {
        **DEFAULT_INTEGRATION_CONFIG["consequentialist"],
        "approval_threshold": 0.75,  # Much stricter
    },
}


def get_config(environment: str = "production") -> Dict[str, Any]:
    """Get configuration for specified environment.

    Args:
        environment: 'production', 'dev', or 'offensive'

    Returns:
        Configuration dict
    """
    configs = {
        "production": PRODUCTION_CONFIG,
        "dev": DEV_CONFIG,
        "development": DEV_CONFIG,
        "offensive": OFFENSIVE_CONFIG,
        "default": DEFAULT_INTEGRATION_CONFIG,
    }

    return configs.get(environment.lower(), DEFAULT_INTEGRATION_CONFIG)


def get_framework_weights(environment: str = "production") -> Dict[str, float]:
    """Get framework weights for environment.

    Args:
        environment: Environment name

    Returns:
        Framework weights dict
    """
    config = get_config(environment)
    return config["framework_weights"]


def get_thresholds(environment: str = "production") -> Dict[str, float]:
    """Get decision thresholds for environment.

    Args:
        environment: Environment name

    Returns:
        Dict with 'approval_threshold' and 'rejection_threshold'
    """
    config = get_config(environment)
    return {
        "approval_threshold": config["approval_threshold"],
        "rejection_threshold": config["rejection_threshold"],
    }


# Risk-level based configuration overrides
RISK_CONFIGS: Dict[str, Dict[str, Any]] = {
    "low": {
        "approval_threshold": 0.60,
        "rejection_threshold": 0.45,
        "veto_enabled": True,
    },
    "medium": {
        "approval_threshold": 0.70,
        "rejection_threshold": 0.40,
        "veto_enabled": True,
    },
    "high": {
        "approval_threshold": 0.80,
        "rejection_threshold": 0.35,
        "veto_enabled": True,
    },
    "critical": {
        "approval_threshold": 0.90,
        "rejection_threshold": 0.25,
        "veto_enabled": True,
        "hitl_escalation_enabled": True,  # Always escalate critical decisions
    },
}


def get_config_for_risk(
    risk_level: str, base_environment: str = "production"
) -> Dict[str, Any]:
    """Get configuration adjusted for risk level.

    Args:
        risk_level: 'low', 'medium', 'high', or 'critical'
        base_environment: Base environment config to start from

    Returns:
        Risk-adjusted configuration
    """
    base_config = get_config(base_environment)
    risk_overrides = RISK_CONFIGS.get(risk_level.lower(), {})

    # Merge base config with risk overrides
    return {**base_config, **risk_overrides}
