from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.metrics import (
    REFLEX_EVENTS_TOTAL,
    ANTIGENS_CAPTURED_TOTAL,
    LYMPHNODE_VALIDATIONS_TOTAL,
    LYMPHNODE_VACCINATIONS_TOTAL,
    record_antigen_capture,
    record_lymphnode_validation,
    record_reflex_event,
    record_vaccination,
)


def get_sample_value(metric, **labels) -> float:
    for family in metric.collect():
        for sample in family.samples:
            if sample.labels == labels:
                return sample.value
    return 0.0


def test_record_reflex_and_antigen_metrics() -> None:
    before_reflex = get_sample_value(REFLEX_EVENTS_TOTAL, signature_id="1")
    before_antigen = get_sample_value(ANTIGENS_CAPTURED_TOTAL, protocol="tcp")

    record_reflex_event("1")
    record_reflex_event("1")
    record_antigen_capture("TCP")

    assert get_sample_value(REFLEX_EVENTS_TOTAL, signature_id="1") == before_reflex + 2.0
    assert get_sample_value(ANTIGENS_CAPTURED_TOTAL, protocol="tcp") == before_antigen + 1.0


def test_record_lymphnode_metrics() -> None:
    confirmed_before = get_sample_value(LYMPHNODE_VALIDATIONS_TOTAL, result="confirmed", severity="high")
    error_before = get_sample_value(LYMPHNODE_VALIDATIONS_TOTAL, result="error", severity="medium")
    vacc_success_before = get_sample_value(LYMPHNODE_VACCINATIONS_TOTAL, result="success")
    vacc_failure_before = get_sample_value(LYMPHNODE_VACCINATIONS_TOTAL, result="failure")

    record_lymphnode_validation("confirmed", "high", 0.2)
    record_lymphnode_validation("error", "medium", 0.4)
    record_vaccination("success")
    record_vaccination("failure")

    assert get_sample_value(LYMPHNODE_VALIDATIONS_TOTAL, result="confirmed", severity="high") == confirmed_before + 1.0
    assert get_sample_value(LYMPHNODE_VALIDATIONS_TOTAL, result="error", severity="medium") == error_before + 1.0
    assert get_sample_value(LYMPHNODE_VACCINATIONS_TOTAL, result="success") == vacc_success_before + 1.0
    assert get_sample_value(LYMPHNODE_VACCINATIONS_TOTAL, result="failure") == vacc_failure_before + 1.0
