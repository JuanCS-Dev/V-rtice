"""Maximus HCL Monitor Service - Package Initialization.

This package provides the core functionality for the Maximus AI's Homeostatic
Control Loop (HCL) Monitor Service. It is responsible for continuously collecting
real-time operational metrics and system state data from various Maximus AI
services and the underlying infrastructure.

Key components within this package are responsible for:
- Interfacing with system-level monitoring tools (e.g., `psutil`, Prometheus).
- Aggregating metrics such as CPU usage, memory consumption, network I/O, and error rates.
- Providing a unified stream of monitoring data to the HCL Analyzer Service.
- Ensuring that the HCL has accurate and up-to-date information for effective
  self-management and adaptive behavior.
"""
