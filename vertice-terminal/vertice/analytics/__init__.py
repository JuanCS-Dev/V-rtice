"""
📊 Advanced Analytics & Machine Learning
Detecção avançada baseada em comportamento e ML

Componentes:
- BehavioralAnalytics: Análise de anomalias comportamentais
- ThreatIntelFeed: Integração com feeds de threat intel
- MLDetector: Detecção baseada em machine learning
- RiskScorer: Cálculo de risk score para assets/users
- HuntingWorkbench: Interface avançada para threat hunting
"""

from .behavioral import BehavioralAnalytics, Baseline, Anomaly, AnomalyType
from .threat_intel import ThreatIntelFeed, IOCType, IOC, ThreatActor
from .ml_detector import MLDetector, MLModel, MLModelType, Prediction
from .risk_scorer import RiskScorer, RiskScore, RiskFactor, RiskLevel

__all__ = [
    "BehavioralAnalytics",
    "Baseline",
    "Anomaly",
    "AnomalyType",
    "ThreatIntelFeed",
    "IOCType",
    "IOC",
    "ThreatActor",
    "MLDetector",
    "MLModel",
    "MLModelType",
    "Prediction",
    "RiskScorer",
    "RiskScore",
    "RiskFactor",
    "RiskLevel",
]
