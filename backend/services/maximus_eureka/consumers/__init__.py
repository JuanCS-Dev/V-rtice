"""
Kafka Consumers Module - MAXIMUS Eureka Adaptive Immunity.

Consumes APVs (Actionable Prioritized Vulnerabilities) from Oráculo Threat Sentinel.
Part of the Active Immune System that provides autonomous vulnerability remediation.

Architectural Significance:
    Consumer layer bridges Oráculo (detection) and Eureka (remediation),
    establishing reactive threat response pathway analogous to immune system's
    antigen recognition → antibody production cascade.

    The consumption model implements at-least-once delivery semantics with
    idempotency guarantees, preventing duplicate remediation attempts while
    ensuring no vulnerability goes unaddressed.
"""

from consumers.apv_consumer import APVConsumer, APVConsumerConfig

__all__ = ["APVConsumer", "APVConsumerConfig"]
