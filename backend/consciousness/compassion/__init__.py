"""
Compassion Module - Event Detection and Intervention Planning

Part of the Ethics & Compassion track for reactive autonomous agents.
Detects suffering events and plans compassionate interventions.
"""

from .event_detector import EventDetector, SufferingEvent, EventType

__all__ = ["EventDetector", "SufferingEvent", "EventType"]
