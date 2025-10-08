"""
Resource Demand Forecaster - SARIMA Time Series Prediction

Predicts CPU/RAM demand at 1h, 6h, 24h horizons using Seasonal ARIMA.
Trained daily on last 30 days of telemetry data.

Performance Targets:
    - R² > 0.7 (1h predictions)
    - R² > 0.5 (24h predictions)
"""

import logging

import pandas as pd
from sklearn.metrics import r2_score
from statsmodels.tsa.statespace.sarimax import SARIMAX

logger = logging.getLogger(__name__)


class ResourceDemandForecaster:
    """
    SARIMA-based time series forecaster for resource demand.

    Implements Seasonal AutoRegressive Integrated Moving Average
    to predict future CPU/Memory usage based on historical patterns.

    Hyperparameters:
        order (p,d,q): (1, 1, 1) - AR, differencing, MA
        seasonal_order (P,D,Q,s): (1, 1, 1, 24) - Seasonal with 24h period
    """

    def __init__(
        self,
        order: tuple[int, int, int] = (1, 1, 1),
        seasonal_order: tuple[int, int, int, int] = (1, 1, 1, 24),
    ):
        """
        Initialize SARIMA forecaster.

        Args:
            order: ARIMA (p, d, q) parameters
            seasonal_order: Seasonal (P, D, Q, s) parameters
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.cpu_model = None
        self.memory_model = None
        self.last_training_data = None

        logger.info(f"ResourceDemandForecaster initialized (order={order}, seasonal_order={seasonal_order})")

    def train(self, historical_data: pd.DataFrame):
        """
        Train SARIMA models on historical telemetry data.

        Args:
            historical_data: DataFrame with columns:
                - timestamp (DatetimeIndex)
                - cpu_usage (float): CPU percentage
                - memory_usage (float): Memory percentage
                - hour_of_day (int): 0-23
                - day_of_week (int): 0-6
                - is_weekend (bool)

        Expected data: Last 30 days with 15-second granularity (172,800 rows)
        """
        try:
            logger.info(f"Training SARIMA models on {len(historical_data)} samples")

            # Ensure datetime index
            if not isinstance(historical_data.index, pd.DatetimeIndex):
                historical_data = historical_data.set_index("timestamp")

            # Exogenous features
            exog = historical_data[["hour_of_day", "day_of_week", "is_weekend"]]

            # Train CPU model
            logger.info("Training CPU demand forecaster...")
            self.cpu_model = SARIMAX(
                historical_data["cpu_usage"],
                exog=exog,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)

            # Train Memory model
            logger.info("Training Memory demand forecaster...")
            self.memory_model = SARIMAX(
                historical_data["memory_usage"],
                exog=exog,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)

            # Store for validation
            self.last_training_data = historical_data

            logger.info("SARIMA training completed successfully")

        except Exception as e:
            logger.error(f"Error training SARIMA models: {e}", exc_info=True)
            raise

    def predict(self, horizon: str = "1h") -> dict[str, list[float]]:
        """
        Forecast resource demand.

        Args:
            horizon: Prediction window ('1h', '6h', '24h')

        Returns:
            Dictionary with 'cpu_forecast' and 'memory_forecast' lists
        """
        if not self.cpu_model or not self.memory_model:
            raise RuntimeError("Models not trained. Call train() first.")

        # Map horizon to steps (15-min intervals)
        steps_map = {
            "1h": 4,  # 4 steps * 15min = 1 hour
            "6h": 24,  # 24 steps * 15min = 6 hours
            "24h": 96,  # 96 steps * 15min = 24 hours
        }

        steps = steps_map.get(horizon, 4)

        try:
            # Generate future exogenous variables
            future_exog = self._generate_future_exog(steps)

            # Forecast CPU
            cpu_forecast = self.cpu_model.forecast(steps=steps, exog=future_exog)

            # Forecast Memory
            memory_forecast = self.memory_model.forecast(steps=steps, exog=future_exog)

            logger.debug(
                f"{horizon} forecast: CPU avg={cpu_forecast.mean():.1f}%, Memory avg={memory_forecast.mean():.1f}%"
            )

            return {
                "cpu_forecast": cpu_forecast.tolist(),
                "memory_forecast": memory_forecast.tolist(),
                "horizon": horizon,
                "steps": steps,
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {e}", exc_info=True)
            raise

    def _generate_future_exog(self, steps: int) -> pd.DataFrame:
        """Generate exogenous variables for future timestamps."""
        # Get last timestamp from training data
        last_timestamp = self.last_training_data.index[-1]

        # Generate future timestamps (15-min intervals)
        future_timestamps = pd.date_range(start=last_timestamp + pd.Timedelta(minutes=15), periods=steps, freq="15min")

        # Create exogenous features
        future_exog = pd.DataFrame(
            {
                "hour_of_day": future_timestamps.hour,
                "day_of_week": future_timestamps.dayofweek,
                "is_weekend": future_timestamps.dayofweek >= 5,
            },
            index=future_timestamps,
        )

        return future_exog

    def validate(self, test_data: pd.DataFrame) -> dict[str, float]:
        """
        Validate model accuracy on test set.

        Args:
            test_data: DataFrame with same format as training data

        Returns:
            Dictionary with R² scores for CPU and Memory
        """
        if not self.cpu_model or not self.memory_model:
            raise RuntimeError("Models not trained. Call train() first.")

        try:
            # Get actual values
            actual_cpu = test_data["cpu_usage"].values
            actual_memory = test_data["memory_usage"].values

            # Generate exog for test period
            exog = test_data[["hour_of_day", "day_of_week", "is_weekend"]]

            # Predict
            pred_cpu = self.cpu_model.forecast(steps=len(test_data), exog=exog)
            pred_memory = self.memory_model.forecast(steps=len(test_data), exog=exog)

            # Calculate R² scores
            cpu_r2 = r2_score(actual_cpu, pred_cpu)
            memory_r2 = r2_score(actual_memory, pred_memory)

            logger.info(f"Validation results: CPU R²={cpu_r2:.3f}, Memory R²={memory_r2:.3f}")

            return {
                "cpu_r2": cpu_r2,
                "memory_r2": memory_r2,
                "meets_target_1h": cpu_r2 > 0.7 and memory_r2 > 0.7,
                "meets_target_24h": cpu_r2 > 0.5 and memory_r2 > 0.5,
            }

        except Exception as e:
            logger.error(f"Error during validation: {e}", exc_info=True)
            raise
