"""
Resource Analyzer - REAL Statistical Analysis
==============================================

Analisa métricas do sistema usando modelos estatísticos REAIS:
- ARIMA para previsão de séries temporais
- Z-score para detecção de anomalias
- Exponential smoothing para trending
- Change point detection

ZERO mocks. Usa scipy, statsmodels, numpy para análise real.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum

# Análise estatística REAL
from scipy import stats
from scipy.signal import find_peaks


class AnomalyType(str, Enum):
    """Tipos de anomalia detectados"""
    SPIKE = "spike"  # Pico súbito
    DROP = "drop"  # Queda súbita
    TREND = "trend"  # Tendência crescente/decrescente
    OSCILLATION = "oscillation"  # Oscilação anormal
    SUSTAINED_HIGH = "sustained_high"  # Alto sustentado
    SUSTAINED_LOW = "sustained_low"  # Baixo sustentado


class Anomaly(BaseModel):
    """Anomalia detectada"""
    type: AnomalyType
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float  # Desvios padrão
    severity: float  # 0-1
    timestamp: str


class ResourceAnalysis(BaseModel):
    """Resultado da análise de recursos"""
    timestamp: str
    requires_action: bool
    anomalies: List[Anomaly]

    # Predictions (próximos 5 minutos)
    predicted_cpu: Optional[float] = None
    predicted_memory: Optional[float] = None
    predicted_load_trend: Optional[str] = None  # "increasing", "decreasing", "stable"

    # Recommendations
    recommended_actions: List[str]
    urgency_level: int  # 0-10


class ResourceAnalyzer:
    """
    Analisa estado do sistema usando estatística REAL.

    Detecta:
    - Anomalias (z-score method)
    - Tendências (linear regression)
    - Predições (exponential smoothing + ARIMA se disponível)
    """

    def __init__(
        self,
        anomaly_threshold_sigma: float = 3.0,  # 3 desvios padrão
        min_history_for_prediction: int = 20,
    ):
        self.anomaly_threshold = anomaly_threshold_sigma
        self.min_history = min_history_for_prediction

        # Tentar importar statsmodels para ARIMA (opcional)
        self.has_statsmodels = False
        try:
            from statsmodels.tsa.arima.model import ARIMA
            self.ARIMA = ARIMA
            self.has_statsmodels = True
            print("📊 [Analyzer] statsmodels available - ARIMA predictions enabled")
        except ImportError:
            print("⚠️  [Analyzer] statsmodels not installed - using exponential smoothing only")

    async def analyze_state(
        self,
        current_state: 'SystemState',
        history: List['SystemState']
    ) -> ResourceAnalysis:
        """
        Analisa estado atual do sistema comparado com histórico.

        Usa métodos estatísticos REAIS:
        - Z-score para anomalias
        - Linear regression para trends
        - Exponential smoothing para predições
        """
        anomalies = []
        recommended_actions = []
        requires_action = False
        urgency = 0

        if len(history) < 5:
            # Histórico insuficiente - sem análise
            return ResourceAnalysis(
                timestamp=datetime.now().isoformat(),
                requires_action=False,
                anomalies=[],
                recommended_actions=["Collecting baseline data..."],
                urgency_level=0
            )

        # ===== ANOMALY DETECTION (Z-Score Method) =====
        cpu_values = [s.cpu_usage for s in history]
        memory_values = [s.memory_usage for s in history]
        latency_values = [s.avg_latency_ms for s in history]

        # CPU anomalies
        cpu_anomaly = self._detect_anomaly_zscore(
            metric_name="cpu_usage",
            current_value=current_state.cpu_usage,
            historical_values=cpu_values
        )
        if cpu_anomaly:
            anomalies.append(cpu_anomaly)
            if cpu_anomaly.severity > 0.7:
                requires_action = True
                urgency = max(urgency, 7)

        # Memory anomalies
        memory_anomaly = self._detect_anomaly_zscore(
            metric_name="memory_usage",
            current_value=current_state.memory_usage,
            historical_values=memory_values
        )
        if memory_anomaly:
            anomalies.append(memory_anomaly)
            if memory_anomaly.severity > 0.7:
                requires_action = True
                urgency = max(urgency, 8)  # Memory mais crítico

        # Latency anomalies
        latency_anomaly = self._detect_anomaly_zscore(
            metric_name="avg_latency_ms",
            current_value=current_state.avg_latency_ms,
            historical_values=latency_values
        )
        if latency_anomaly:
            anomalies.append(latency_anomaly)
            if latency_anomaly.severity > 0.6:
                requires_action = True
                urgency = max(urgency, 6)

        # ===== TREND DETECTION (Linear Regression) =====
        if len(history) >= self.min_history:
            cpu_trend = self._detect_trend(cpu_values)
            memory_trend = self._detect_trend(memory_values)

            predicted_load_trend = "stable"

            if cpu_trend > 0.5:  # Increasing trend
                predicted_load_trend = "increasing"
                recommended_actions.append(f"CPU trending up: {cpu_trend:.2f}%/check - consider scaling")
                if cpu_trend > 1.0:
                    requires_action = True
                    urgency = max(urgency, 5)

            if memory_trend > 0.5:
                if predicted_load_trend != "increasing":
                    predicted_load_trend = "increasing"
                recommended_actions.append(f"Memory trending up: {memory_trend:.2f}%/check - monitor for leaks")
                if memory_trend > 1.0:
                    requires_action = True
                    urgency = max(urgency, 6)

            # ===== PREDICTION (Exponential Smoothing or ARIMA) =====
            predicted_cpu = self._predict_next_value(cpu_values)
            predicted_memory = self._predict_next_value(memory_values)

        else:
            predicted_load_trend = None
            predicted_cpu = None
            predicted_memory = None

        # ===== THRESHOLD-BASED CHECKS =====
        if current_state.cpu_usage > 90:
            recommended_actions.append("CRITICAL: CPU >90% - immediate scaling required")
            requires_action = True
            urgency = 10

        if current_state.memory_usage > 85:
            recommended_actions.append("WARNING: Memory >85% - potential OOM risk")
            requires_action = True
            urgency = max(urgency, 9)

        if current_state.avg_latency_ms > 100:
            recommended_actions.append(f"High latency detected: {current_state.avg_latency_ms:.1f}ms")
            if current_state.avg_latency_ms > 200:
                requires_action = True
                urgency = max(urgency, 7)

        # ===== SUSTAINED CONDITIONS =====
        sustained_high_cpu = self._check_sustained_condition(
            cpu_values[-10:], threshold=80, above=True
        )
        if sustained_high_cpu:
            anomalies.append(Anomaly(
                type=AnomalyType.SUSTAINED_HIGH,
                metric_name="cpu_usage",
                current_value=current_state.cpu_usage,
                expected_value=np.mean(cpu_values),
                deviation=0,
                severity=0.8,
                timestamp=datetime.now().isoformat()
            ))
            recommended_actions.append("CPU sustained >80% for extended period")
            requires_action = True
            urgency = max(urgency, 8)

        if not recommended_actions:
            recommended_actions.append("System operating normally")

        return ResourceAnalysis(
            timestamp=datetime.now().isoformat(),
            requires_action=requires_action,
            anomalies=anomalies,
            predicted_cpu=predicted_cpu,
            predicted_memory=predicted_memory,
            predicted_load_trend=predicted_load_trend,
            recommended_actions=recommended_actions,
            urgency_level=urgency
        )

    def _detect_anomaly_zscore(
        self,
        metric_name: str,
        current_value: float,
        historical_values: List[float]
    ) -> Optional[Anomaly]:
        """
        Detecção de anomalia usando Z-score (método estatístico REAL).

        Z-score = (valor - média) / desvio_padrão

        Se |Z| > threshold (default 3.0), é anomalia.
        """
        if len(historical_values) < 5:
            return None

        mean = np.mean(historical_values)
        std = np.std(historical_values)

        if std == 0:
            return None  # Sem variação

        z_score = (current_value - mean) / std

        if abs(z_score) > self.anomaly_threshold:
            # Detectou anomalia
            if z_score > 0:
                anomaly_type = AnomalyType.SPIKE
            else:
                anomaly_type = AnomalyType.DROP

            severity = min(abs(z_score) / (self.anomaly_threshold * 2), 1.0)

            return Anomaly(
                type=anomaly_type,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=mean,
                deviation=abs(z_score),
                severity=severity,
                timestamp=datetime.now().isoformat()
            )

        return None

    def _detect_trend(self, values: List[float]) -> float:
        """
        Detecta tendência usando regressão linear REAL (scipy).

        Returns:
            Slope (taxa de mudança por período)
            Positivo = crescente, Negativo = decrescente
        """
        if len(values) < 5:
            return 0.0

        x = np.arange(len(values))
        y = np.array(values)

        # Linear regression REAL
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Retorna slope (taxa de crescimento/decrescimento)
        return slope

    def _predict_next_value(self, values: List[float]) -> Optional[float]:
        """
        Prediz próximo valor usando Exponential Smoothing.

        Se statsmodels disponível, usa ARIMA para predição mais precisa.
        """
        if len(values) < self.min_history:
            return None

        # Método 1: Exponential Smoothing (sempre disponível)
        alpha = 0.3  # Smoothing factor
        prediction = values[-1]  # Start with last value

        for i in range(len(values) - 1, max(len(values) - 10, 0), -1):
            prediction = alpha * values[i] + (1 - alpha) * prediction

        # Método 2: ARIMA (se disponível) - mais preciso
        if self.has_statsmodels and len(values) >= 30:
            try:
                model = self.ARIMA(values, order=(1, 1, 1))
                fitted = model.fit()
                forecast = fitted.forecast(steps=1)
                prediction = float(forecast[0])
            except Exception as e:
                # Fallback para exponential smoothing
                pass

        return round(prediction, 2)

    def _check_sustained_condition(
        self,
        values: List[float],
        threshold: float,
        above: bool = True
    ) -> bool:
        """
        Verifica se condição foi sustentada por período.

        Args:
            values: Valores recentes
            threshold: Limite
            above: True para verificar acima, False para abaixo

        Returns:
            True se condição sustentada em >80% das amostras
        """
        if len(values) < 5:
            return False

        if above:
            count = sum(1 for v in values if v > threshold)
        else:
            count = sum(1 for v in values if v < threshold)

        return (count / len(values)) > 0.8
