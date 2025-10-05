"""Maximus HPC Service - Bayesian Core.

This module implements the Bayesian Core for the Maximus AI's High-Performance
Computing (HPC) Service. It forms the probabilistic foundation for the Active
Inference Engine, maintaining and updating the AI's beliefs about its environment
and potential threats.

Key functionalities include:
- Representing the AI's internal model of the world as a probabilistic distribution.
- Generating top-down predictions based on current beliefs.
- Computing prediction errors when new observations arrive.
- Updating beliefs (performing Bayesian inference) to minimize prediction error.

This core is crucial for Maximus AI's ability to learn, adapt, and make informed
decisions under uncertainty, enabling sophisticated threat prediction and
autonomous security operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
from pydantic import BaseModel


class Observation(BaseModel):
    """Represents a single observation from the environment.

    Attributes:
        timestamp (int): Timestamp of the observation.
        features (np.ndarray): Numerical features of the observation.
        source_id (str): Identifier of the source of the observation.
    """
    timestamp: int
    features: np.ndarray
    source_id: str

    class Config:
        arbitrary_types_allowed = True


class BeliefState(BaseModel):
    """Represents the current belief state of the Bayesian Core.

    Attributes:
        mean (np.ndarray): The mean of the belief distribution.
        covariance (np.ndarray): The covariance of the belief distribution.
        entropy (float): The entropy of the belief state, indicating uncertainty.
        timestamp (str): ISO formatted timestamp of the last update.
    """
    mean: np.ndarray
    covariance: np.ndarray
    entropy: float
    timestamp: str

    class Config:
        arbitrary_types_allowed = True


class PredictionError(BaseModel):
    """Represents the prediction error between a prediction and an observation.

    Attributes:
        error_vector (np.ndarray): The vector difference between observation and prediction.
        magnitude (float): The scalar magnitude of the prediction error.
        timestamp (str): ISO formatted timestamp of when the error was computed.
    """
    error_vector: np.ndarray
    magnitude: float
    timestamp: str

    class Config:
        arbitrary_types_allowed = True


class BayesianCore:
    """Maintains and updates the AI's beliefs about its environment and potential threats.

    Forms the probabilistic foundation for the Active Inference Engine.
    """

    def __init__(self, num_features: int, initial_uncertainty: float = 1.0):
        """Initializes the BayesianCore.

        Args:
            num_features (int): The number of features in the observation space.
            initial_uncertainty (float): The initial uncertainty of the belief state.
        """
        self.num_features = num_features
        self.belief_state: Optional[BeliefState] = None
        self.prior_mean: Optional[np.ndarray] = None
        self.prior_covariance: Optional[np.ndarray] = None
        self.initial_uncertainty = initial_uncertainty
        print("[BayesianCore] Initialized Bayesian Core.")

    def learn_prior(self, normal_observations: List[Observation]):
        """Learns the prior belief state from a set of normal observations.

        Args:
            normal_observations (List[Observation]): A list of observations representing normal system behavior.
        
        Raises:
            ValueError: If no observations are provided or features do not match num_features.
        """
        if not normal_observations:
            raise ValueError("Cannot learn prior from empty observations.")
        
        features_matrix = np.array([obs.features for obs in normal_observations])
        if features_matrix.shape[1] != self.num_features:
            raise ValueError(f"Observation features ({features_matrix.shape[1]}) do not match expected num_features ({self.num_features}).")

        self.prior_mean = np.mean(features_matrix, axis=0)
        self.prior_covariance = np.cov(features_matrix, rowvar=False) + np.eye(self.num_features) * 1e-6 # Add small value for stability
        
        # Initialize belief state with prior
        self.belief_state = BeliefState(
            mean=self.prior_mean,
            covariance=self.prior_covariance,
            entropy=self._calculate_entropy(self.prior_covariance),
            timestamp=datetime.now().isoformat()
        )
        print(f"[BayesianCore] Prior learned from {len(normal_observations)} observations.")

    def predict(self) -> Dict[str, Any]:
        """Generates a top-down prediction based on the current belief state.

        Returns:
            Dict[str, Any]: A dictionary containing the predicted state and its uncertainty.
        
        Raises:
            RuntimeError: If the prior has not been learned yet.
        """
        if not self.belief_state:
            raise RuntimeError("Prior not learned. Call learn_prior first.")
        
        # In a full predictive coding model, this would involve a generative model
        # to produce a prediction from the latent belief state.
        # For simplicity, we return the mean of the belief state as the prediction.
        print("[BayesianCore] Generating prediction from current belief state.")
        return {
            "predicted_state": self.belief_state.mean,
            "predicted_uncertainty": np.diag(self.belief_state.covariance),
            "timestamp": datetime.now().isoformat()
        }

    def compute_prediction_error(self, observation: Observation, prediction: Dict[str, Any]) -> PredictionError:
        """Computes the prediction error between an observation and a prediction.

        Args:
            observation (Observation): The new observation.
            prediction (Dict[str, Any]): The prediction from the model.

        Returns:
            PredictionError: The computed prediction error.
        
        Raises:
            ValueError: If observation features do not match prediction dimensions.
        """
        predicted_state = prediction["predicted_state"]
        if observation.features.shape != predicted_state.shape:
            raise ValueError("Observation features and prediction dimensions do not match.")

        error_vector = observation.features - predicted_state
        magnitude = np.linalg.norm(error_vector)
        print(f"[BayesianCore] Computed prediction error with magnitude: {magnitude:.4f}")
        return PredictionError(
            error_vector=error_vector,
            magnitude=magnitude,
            timestamp=datetime.now().isoformat()
        )

    def update_beliefs(self, observation: Observation, prediction_error: PredictionError) -> BeliefState:
        """Updates the belief state based on the prediction error (Bayesian inference).

        Args:
            observation (Observation): The new observation.
            prediction_error (PredictionError): The computed prediction error.

        Returns:
            BeliefState: The updated belief state.
        
        Raises:
            RuntimeError: If the prior has not been learned yet.
        """
        if not self.belief_state:
            raise RuntimeError("Prior not learned. Call learn_prior first.")

        # Simplified Bayesian update (e.g., Kalman filter-like update)
        # This is a highly simplified representation of a complex Bayesian update.
        # In a real system, this would involve more sophisticated probabilistic inference.
        
        # Update mean towards the observation, weighted by uncertainty
        kalman_gain = self.belief_state.covariance @ np.linalg.inv(self.belief_state.covariance + np.eye(self.num_features) * self.initial_uncertainty)
        new_mean = self.belief_state.mean + kalman_gain @ prediction_error.error_vector
        new_covariance = (np.eye(self.num_features) - kalman_gain) @ self.belief_state.covariance

        self.belief_state = BeliefState(
            mean=new_mean,
            covariance=new_covariance,
            entropy=self._calculate_entropy(new_covariance),
            timestamp=datetime.now().isoformat()
        )
        print(f"[BayesianCore] Beliefs updated. New entropy: {self.belief_state.entropy:.4f}")
        return self.belief_state

    def _calculate_entropy(self, covariance_matrix: np.ndarray) -> float:
        """Calculates the entropy of a multivariate Gaussian distribution from its covariance matrix.

        Args:
            covariance_matrix (np.ndarray): The covariance matrix of the distribution.

        Returns:
            float: The entropy value.
        """
        # Entropy of a multivariate Gaussian distribution
        # H = 0.5 * log( (2 * pi * e)^k * det(Sigma) )
        # where k is dimension, Sigma is covariance
        sign, logdet = np.linalg.slogdet(covariance_matrix)
        if sign == -1:
            # This indicates a singular or near-singular matrix, which can happen with mock data
            # In a real system, this would require more robust handling or regularization
            return np.inf # Indicate very high uncertainty
        return 0.5 * (self.num_features * (1.0 + np.log(2 * np.pi)) + logdet)

    def get_belief_state(self) -> Optional[BeliefState]:
        """Returns the current belief state of the system.

        Returns:
            Optional[BeliefState]: The current BeliefState object, or None if not initialized.
        """
        return self.belief_state
