"""Tests for VÉRTICE Ethical Audit Service.

Comprehensive test suite following PAGANI Standard:
- NO mocking of internal business logic
- External dependencies mocked (PostgreSQL, Auth)
- 95%+ coverage target
- Modular test organization by functional domain

Test Modules:
- test_core_audit.py: Core ethical decision logging, overrides, metrics
- test_analytics.py: Timeline and risk heatmap analytics
- test_xai.py: Explainability features
- test_fairness.py: Fairness evaluation and mitigation
- test_privacy.py: Differential privacy
- test_federated_learning.py: FL coordinator
- test_hitl.py: Human-in-the-loop workflows
- test_compliance.py: Compliance checks and evidence
"""
