"""Operational Mode Definitions - Sympathetic/Parasympathetic Analogy"""

OPERATIONAL_MODES = {
    "HIGH_PERFORMANCE": {
        "trigger": "high_traffic OR critical_alert OR sla_risk",
        "policy": {
            "cpu_allocation": None,  # No limits (burst mode)
            "memory_allocation": 1.5,  # Over-provision 150%
            "gpu_priority": "preemptive",
            "cache_strategy": "aggressive",  # Redis maxmemory=80%
            "db_connections": "max",
            "log_level": "ERROR",
            "background_jobs": "DISABLED",
        },
        "cost": "high",
        "description": "Sympathetic mode - prioritize availability over cost",
    },
    "ENERGY_EFFICIENT": {
        "trigger": "low_traffic AND no_alerts AND off_peak_hours",
        "policy": {
            "cpu_allocation": 0.5,  # Throttled to 50%
            "memory_allocation": 1.0,  # Right-sized
            "gpu_priority": "batch_only",
            "cache_strategy": "conservative",  # Redis maxmemory=40%
            "db_connections": "min",
            "log_level": "DEBUG",
            "background_jobs": "ENABLED",  # Model retraining, cleanup
        },
        "cost": "low",
        "description": "Parasympathetic mode - prioritize cost savings",
    },
    "BALANCED": {
        "trigger": "default",
        "policy": {
            "cpu_allocation": 0.75,
            "memory_allocation": 1.2,
            "gpu_priority": "normal",
            "cache_strategy": "balanced",
            "db_connections": "normal",
            "log_level": "INFO",
            "background_jobs": "THROTTLED",
        },
        "cost": "medium",
        "description": "Balanced mode - interpolation between high/efficient",
    },
}


def get_mode_policy(mode: str):
    """Get the policy configuration for a given operational mode.

    Args:
        mode: One of 'HIGH_PERFORMANCE', 'ENERGY_EFFICIENT', or 'BALANCED'

    Returns:
        The policy dict for the specified mode

    Raises:
        KeyError: If the mode is not defined
    """
    return OPERATIONAL_MODES[mode]["policy"]
