"""Maximus AI Immune System - Circuit Breaker Module.

This module implements a circuit breaker pattern for the Maximus AI Immune
System. It is designed to prevent cascading failures in a distributed system
by temporarily halting requests to services that are experiencing issues.

When a service is detected as unhealthy or anomalous (e.g., by the Consensus
Validator), the circuit breaker 'trips', preventing further requests from being
sent to that service. After a configurable cooldown period, the circuit breaker
will 'half-open', allowing a limited number of test requests to determine if the
service has recovered. This pattern enhances the overall resilience and stability
of the Maximus AI system.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class CircuitBreaker:
    """Implements a circuit breaker pattern to prevent cascading failures.

    Temporarily halts requests to services experiencing issues, enhancing
    the overall resilience and stability of the Maximus AI system.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 30, reset_timeout_seconds: int = 60):
        """Initializes the CircuitBreaker.

        Args:
            failure_threshold (int): Number of consecutive failures before tripping.
            cooldown_seconds (int): Time in seconds to stay in 'open' state.
            reset_timeout_seconds (int): Time in seconds to wait in 'half-open' state before full reset.
        """
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.reset_timeout_seconds = reset_timeout_seconds
        self.services: Dict[str, Dict[str, Any]] = {}

    def _get_service_state(self, service_id: str) -> Dict[str, Any]:
        """Retrieves or initializes the state for a given service ID."""
        if service_id not in self.services:
            self.services[service_id] = {
                "state": "closed", # closed, open, half-open
                "failures": 0,
                "last_failure_time": None,
                "last_trip_time": None
            }
        return self.services[service_id]

    def trip(self, service_id: str):
        """Trips the circuit breaker for a service, moving it to the 'open' state.

        Args:
            service_id (str): The ID of the service to trip.
        """
        state = self._get_service_state(service_id)
        state["failures"] += 1
        state["last_failure_time"] = datetime.now()

        if state["state"] == "closed" and state["failures"] >= self.failure_threshold:
            state["state"] = "open"
            state["last_trip_time"] = datetime.now()
            print(f"[CircuitBreaker] Circuit tripped for service: {service_id}")

    def reset(self, service_id: str):
        """Resets the circuit breaker for a service, moving it to the 'closed' state.

        Args:
            service_id (str): The ID of the service to reset.
        """
        state = self._get_service_state(service_id)
        state["state"] = "closed"
        state["failures"] = 0
        state["last_failure_time"] = None
        state["last_trip_time"] = None
        print(f"[CircuitBreaker] Circuit reset for service: {service_id}")

    def half_open(self, service_id: str):
        """Moves the circuit breaker to the 'half-open' state.

        Args:
            service_id (str): The ID of the service to half-open.
        """
        state = self._get_service_state(service_id)
        state["state"] = "half-open"
        print(f"[CircuitBreaker] Circuit half-open for service: {service_id}")

    def allow_request(self, service_id: str) -> bool:
        """Determines if a request is allowed to proceed to the service.

        Args:
            service_id (str): The ID of the service.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        state = self._get_service_state(service_id)
        current_time = datetime.now()

        if state["state"] == "closed":
            return True
        elif state["state"] == "open":
            if state["last_trip_time"] and (current_time - state["last_trip_time"]) > timedelta(seconds=self.cooldown_seconds):
                self.half_open(service_id)
                return True # Allow one test request
            return False
        elif state["state"] == "half-open":
            # In half-open, allow one request, if it fails, go back to open.
            # If it succeeds, reset to closed.
            # For simplicity, we'll just allow one and expect external reset/trip.
            return True
        return False

    def get_status(self, service_id: str) -> Dict[str, Any]:
        """Retrieves the current status of the circuit breaker for a service.

        Args:
            service_id (str): The ID of the service.

        Returns:
            Dict[str, Any]: A dictionary containing the circuit breaker's state and related metrics.
        """
        state = self._get_service_state(service_id)
        return {
            "service_id": service_id,
            "state": state["state"],
            "failures": state["failures"],
            "last_failure_time": state["last_failure_time"].isoformat() if state["last_failure_time"] else None,
            "last_trip_time": state["last_trip_time"].isoformat() if state["last_trip_time"] else None
        }
