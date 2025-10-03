"""
HCL Analyzer - Predictive Models
=================================
Real ML models for prediction and anomaly detection:
- SARIMA: Time-series forecasting (CPU, RAM, GPU)
- Isolation Forest: Anomaly detection
- XGBoost: Failure prediction
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import pickle
import joblib
from pathlib import Path

# Time-series forecasting
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

# Anomaly detection
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Failure prediction
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

logger = logging.getLogger(__name__)


class SARIMAForecaster:
    """
    SARIMA model for time-series forecasting.
    Predicts CPU/Memory/GPU usage for next 1h, 6h, 24h.
    """

    def __init__(self, metric_name: str, order=(1, 1, 1), seasonal_order=(1, 1, 1, 24)):
        """
        Args:
            metric_name: Name of metric to forecast
            order: (p, d, q) for ARIMA
            seasonal_order: (P, D, Q, s) for seasonal component
        """
        self.metric_name = metric_name
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.scaler = StandardScaler()
        self.last_trained = None

    def check_stationarity(self, series: pd.Series) -> Tuple[bool, float]:
        """Check if time series is stationary using ADF test"""
        result = adfuller(series.dropna())
        p_value = result[1]
        is_stationary = p_value < 0.05
        return is_stationary, p_value

    def prepare_data(self, df: pd.DataFrame) -> pd.Series:
        """
        Prepare data for training.

        Args:
            df: DataFrame with columns [timestamp, metric_value]

        Returns:
            Time-indexed series
        """
        # Sort by timestamp
        df = df.sort_values('timestamp')

        # Set timestamp as index
        df.set_index('timestamp', inplace=True)

        # Resample to hourly (fill missing with interpolation)
        series = df['metric_value'].resample('1H').mean().interpolate(method='time')

        return series

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Train SARIMA model.

        Args:
            df: Historical data (min 7 days recommended)

        Returns:
            Training metrics
        """
        logger.info(f"Training SARIMA for {self.metric_name}")

        # Prepare data
        series = self.prepare_data(df)

        # Check stationarity
        is_stationary, p_value = self.check_stationarity(series)
        logger.info(f"Stationarity test: p-value={p_value:.4f}, stationary={is_stationary}")

        # Train model
        try:
            self.model = SARIMAX(
                series,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            self.fitted_model = self.model.fit(disp=False, maxiter=200)
            self.last_trained = datetime.utcnow()

            # Calculate metrics
            predictions = self.fitted_model.fittedvalues
            residuals = series - predictions

            mae = np.mean(np.abs(residuals))
            rmse = np.sqrt(np.mean(residuals**2))
            mape = np.mean(np.abs(residuals / series)) * 100

            metrics = {
                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "aic": float(self.fitted_model.aic),
                "bic": float(self.fitted_model.bic)
            }

            logger.info(f"Training complete: MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%")
            return metrics

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    def predict(self, steps: int = 24) -> Dict[str, List[float]]:
        """
        Forecast future values.

        Args:
            steps: Number of hours to forecast

        Returns:
            Dictionary with predictions and confidence intervals
        """
        if not self.fitted_model:
            raise ValueError("Model not trained. Call train() first.")

        # Forecast
        forecast = self.fitted_model.get_forecast(steps=steps)

        # Get predictions and confidence intervals
        predictions = forecast.predicted_mean
        conf_int = forecast.conf_int(alpha=0.05)  # 95% confidence

        return {
            "predictions": predictions.tolist(),
            "lower_bound": conf_int.iloc[:, 0].tolist(),
            "upper_bound": conf_int.iloc[:, 1].tolist(),
            "timestamps": [
                (self.last_trained + timedelta(hours=i)).isoformat()
                for i in range(1, steps + 1)
            ]
        }

    def save(self, path: str):
        """Save model to disk"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self.fitted_model, f)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            self.fitted_model = pickle.load(f)
        logger.info(f"Model loaded from {path}")


class IsolationForestDetector:
    """
    Isolation Forest for anomaly detection.
    Detects unusual patterns in system metrics.
    """

    def __init__(self, contamination: float = 0.01, n_estimators: int = 100):
        """
        Args:
            contamination: Expected proportion of anomalies (0.01 = 1%)
            n_estimators: Number of trees
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.feature_names = None
        self.last_trained = None

    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features from metrics data.

        Args:
            df: DataFrame with columns [timestamp, cpu_usage, memory_usage, ...]

        Returns:
            Feature matrix
        """
        features = []

        # Basic stats
        if 'cpu_usage' in df.columns:
            features.append(df['cpu_usage'].values)
        if 'memory_usage' in df.columns:
            features.append(df['memory_usage'].values)
        if 'gpu_usage' in df.columns:
            features.append(df['gpu_usage'].values)
        if 'network_latency' in df.columns:
            features.append(df['network_latency'].values)
        if 'error_rate' in df.columns:
            features.append(df['error_rate'].values)

        # Rolling statistics (if enough data)
        if len(df) > 10:
            features.append(df['cpu_usage'].rolling(5).mean().fillna(0).values)
            features.append(df['cpu_usage'].rolling(5).std().fillna(0).values)

        # Time-based features
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        features.append(df['hour'].values)
        features.append(df['day_of_week'].values)

        return np.column_stack(features)

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Train Isolation Forest on normal data.

        Args:
            df: Historical normal data (should not contain anomalies)

        Returns:
            Training metrics
        """
        logger.info("Training Isolation Forest")

        # Extract features
        X = self.extract_features(df)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled)
        self.last_trained = datetime.utcnow()

        # Calculate metrics on training data
        scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)

        # Count anomalies detected
        n_anomalies = np.sum(predictions == -1)
        anomaly_rate = n_anomalies / len(predictions)

        metrics = {
            "samples_trained": len(X),
            "features": X.shape[1],
            "anomalies_detected": int(n_anomalies),
            "anomaly_rate": float(anomaly_rate),
            "avg_anomaly_score": float(np.mean(scores[predictions == -1])) if n_anomalies > 0 else 0.0
        }

        logger.info(f"Training complete: {n_anomalies} anomalies detected ({anomaly_rate*100:.2f}%)")
        return metrics

    def predict(self, df: pd.DataFrame) -> Dict[str, List]:
        """
        Detect anomalies in new data.

        Args:
            df: New data to check

        Returns:
            Anomaly scores and predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Extract features
        X = self.extract_features(df)
        X_scaled = self.scaler.transform(X)

        # Predict
        scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)

        # Convert to boolean (True = anomaly)
        is_anomaly = predictions == -1

        return {
            "timestamps": df['timestamp'].tolist(),
            "anomaly_scores": scores.tolist(),
            "is_anomaly": is_anomaly.tolist(),
            "n_anomalies": int(np.sum(is_anomaly))
        }

    def save(self, path: str):
        """Save model to disk"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from disk"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        logger.info(f"Model loaded from {path}")


class XGBoostFailurePredictor:
    """
    XGBoost for failure prediction.
    Predicts service failures 10-30 minutes in advance.
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.last_trained = None

    def engineer_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Engineer features from metrics.

        Args:
            df: DataFrame with columns [timestamp, metrics..., failure (0/1)]

        Returns:
            X (features), y (labels)
        """
        features = []

        # Current metrics
        feature_cols = [
            'cpu_usage', 'memory_usage', 'gpu_usage',
            'network_latency', 'error_rate', 'request_queue_depth'
        ]

        for col in feature_cols:
            if col in df.columns:
                features.append(df[col].values)
                self.feature_names.append(col)

        # Trend features (rate of change)
        if len(df) > 5:
            for col in ['cpu_usage', 'memory_usage', 'error_rate']:
                if col in df.columns:
                    trend = df[col].diff().fillna(0).values
                    features.append(trend)
                    self.feature_names.append(f"{col}_trend")

        # Rolling statistics
        if len(df) > 10:
            for col in ['cpu_usage', 'error_rate']:
                if col in df.columns:
                    rolling_mean = df[col].rolling(5).mean().fillna(0).values
                    rolling_std = df[col].rolling(5).std().fillna(0).values
                    features.append(rolling_mean)
                    features.append(rolling_std)
                    self.feature_names.append(f"{col}_rolling_mean")
                    self.feature_names.append(f"{col}_rolling_std")

        # Time features
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        features.append(df['hour'].values)
        self.feature_names.append('hour')

        X = np.column_stack(features)
        y = df['failure'].values if 'failure' in df.columns else None

        return X, y

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Train XGBoost model.

        Args:
            df: Training data with 'failure' column (0=normal, 1=failure)

        Returns:
            Training metrics
        """
        logger.info("Training XGBoost Failure Predictor")

        # Engineer features
        X, y = self.engineer_features(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Handle class imbalance
        scale_pos_weight = np.sum(y_train == 0) / np.sum(y_train == 1)

        # Train model
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            n_jobs=-1,
            eval_metric='auc'
        )

        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )

        self.last_trained = datetime.utcnow()

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "auc_roc": float(roc_auc_score(y_test, y_pred_proba)),
            "n_train": len(X_train),
            "n_test": len(X_test)
        }

        logger.info(f"Training complete: AUC-ROC={metrics['auc_roc']:.3f}, "
                   f"Precision={metrics['precision']:.3f}, Recall={metrics['recall']:.3f}")

        return metrics

    def predict(self, df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, List]:
        """
        Predict failures.

        Args:
            df: Data to predict on
            threshold: Probability threshold for failure (0.5 = 50%)

        Returns:
            Predictions and probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Engineer features
        X, _ = self.engineer_features(df)
        X_scaled = self.scaler.transform(X)

        # Predict
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        predictions = (probabilities >= threshold).astype(int)

        return {
            "timestamps": df['timestamp'].tolist(),
            "failure_probability": probabilities.tolist(),
            "predicted_failure": predictions.tolist(),
            "n_predicted_failures": int(np.sum(predictions))
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if self.model is None:
            return {}

        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance.tolist()))

    def save(self, path: str):
        """Save model to disk"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from disk"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        logger.info(f"Model loaded from {path}")
