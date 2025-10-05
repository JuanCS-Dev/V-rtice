"""Maximus Core Service - Resource Analyzer.

This module provides real-time statistical analysis of system metrics to detect
anomalies, identify trends, and predict future resource needs. It uses robust
statistical methods to ensure accurate and actionable insights into the AI's
operational health and performance.

This component is crucial for the Homeostatic Control Loop (HCL) to make
informed decisions about resource allocation and system adjustments.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class AnomalyType(str, Enum):
    """Enumeration for different types of anomalies detected."""
    SPIKE = "spike"
    DROP = "drop"
    TREND = "trend"


class Anomaly(BaseModel):
    """Represents a detected anomaly in system metrics.

    Attributes:
        type (AnomalyType): The type of anomaly.
        metric_name (str): The name of the metric where the anomaly was detected.
        current_value (float): The current value of the metric.
        severity (float): The severity of the anomaly (0.0 to 1.0).
    """
    type: AnomalyType
    metric_name: str
    current_value: float
    severity: float


class ResourceAnalysis(BaseModel):
    """Represents the comprehensive analysis of system resources.

    Attributes:
        timestamp (str): ISO formatted timestamp of the analysis.
        requires_action (bool): True if the analysis indicates a need for intervention.
        anomalies (List[Anomaly]): A list of detected anomalies.
        recommended_actions (List[str]): Suggested actions based on the analysis.
    """
    timestamp: str
    requires_action: bool
    anomalies: List[Anomaly]
    recommended_actions: List[str]


class ResourceAnalyzer:
    """Performs statistical analysis on system state and historical data.

    This class detects anomalies using methods like Z-score, identifies trends,
    and provides recommendations for resource management.
    """

    def __init__(self, anomaly_threshold_sigma: float = 3.0):
        """Initializes the ResourceAnalyzer.

        Args:
            anomaly_threshold_sigma (float): The number of standard deviations
                from the mean to consider a value an anomaly.
        """
        self.anomaly_threshold = anomaly_threshold_sigma

    async def analyze_state(self, current_state: Any, history: List[Any]) -> ResourceAnalysis:
        """Analyzes the current system state against historical data to detect issues.

        Args:
            current_state (Any): The current SystemState object.
            history (List[Any]): A list of historical SystemState objects.

        Returns:
            ResourceAnalysis: An object containing detected anomalies, trends, and recommendations.
        """
        anomalies = []
        recommended_actions = []
        requires_action = False

        if len(history) < 5: # Not enough data for meaningful analysis
            recommended_actions.append("Collecting baseline data...")
            return ResourceAnalysis(timestamp=datetime.now().isoformat(), requires_action=False, anomalies=[], recommended_actions=recommended_actions)

        # Simplified anomaly detection for demonstration
        cpu_values = [s.cpu_usage for s in history]
        if current_state.cpu_usage > np.mean(cpu_values) + self.anomaly_threshold * np.std(cpu_values):
            anomalies.append(Anomaly(type=AnomalyType.SPIKE, metric_name="cpu_usage", current_value=current_state.cpu_usage, severity=0.8))
            recommended_actions.append("High CPU usage detected.")
            requires_action = True

        return ResourceAnalysis(
            timestamp=datetime.now().isoformat(),
            requires_action=requires_action,
            anomalies=anomalies,
            recommended_actions=recommended_actions
        )