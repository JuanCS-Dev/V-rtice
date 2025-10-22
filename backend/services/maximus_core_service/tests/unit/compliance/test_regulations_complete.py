"""
FASE A - Complete tests for compliance/regulations.py
Target: 80.0% → 95%+ (3 missing lines)
Zero mocks - Padrão Pagani Absoluto
EM NOME DE JESUS!
"""

import pytest
from datetime import datetime
from compliance.regulations import (
    get_regulation,
    REGULATION_REGISTRY,
    EU_AI_ACT,
    GDPR,
    NIST_AI_RMF,
    US_EO_14110,
    BRAZIL_LGPD,
    ISO_27001,
    SOC2_TYPE_II,
    IEEE_7000,
)
from compliance.base import RegulationType


class TestGetRegulation:
    """Test get_regulation function."""

    def test_get_regulation_eu_ai_act(self):
        """Test retrieving EU AI Act regulation."""
        reg = get_regulation(RegulationType.EU_AI_ACT)
        assert reg == EU_AI_ACT
        assert reg.name == "EU Artificial Intelligence Act - High-Risk AI Systems"
        assert reg.jurisdiction == "European Union"

    def test_get_regulation_gdpr(self):
        """Test retrieving GDPR regulation."""
        reg = get_regulation(RegulationType.GDPR)
        assert reg == GDPR
        assert "General Data Protection Regulation" in reg.name
        assert reg.jurisdiction == "European Union"

    def test_get_regulation_nist_ai_rmf(self):
        """Test retrieving NIST AI RMF regulation."""
        reg = get_regulation(RegulationType.NIST_AI_RMF)
        assert reg == NIST_AI_RMF
        assert "NIST" in reg.name
        assert reg.jurisdiction == "United States (voluntary)"

    def test_get_regulation_us_eo_14110(self):
        """Test retrieving US Executive Order 14110."""
        reg = get_regulation(RegulationType.US_EO_14110)
        assert reg == US_EO_14110
        assert "Executive Order" in reg.name
        assert reg.jurisdiction == "United States"

    def test_get_regulation_brazil_lgpd(self):
        """Test retrieving Brazil LGPD regulation."""
        reg = get_regulation(RegulationType.BRAZIL_LGPD)
        assert reg == BRAZIL_LGPD
        assert "LGPD" in reg.name
        assert reg.jurisdiction == "Brazil"

    def test_get_regulation_iso_27001(self):
        """Test retrieving ISO 27001 regulation."""
        reg = get_regulation(RegulationType.ISO_27001)
        assert reg == ISO_27001
        assert "ISO" in reg.name
        assert reg.jurisdiction == "International"

    def test_get_regulation_soc2_type_ii(self):
        """Test retrieving SOC2 Type II regulation."""
        reg = get_regulation(RegulationType.SOC2_TYPE_II)
        assert reg == SOC2_TYPE_II
        assert "SOC 2" in reg.name
        assert "United States" in reg.jurisdiction

    def test_get_regulation_ieee_7000(self):
        """Test retrieving IEEE 7000 regulation."""
        reg = get_regulation(RegulationType.IEEE_7000)
        assert reg == IEEE_7000
        assert "IEEE 7000" in reg.name
        assert reg.jurisdiction == "International"

    def test_get_regulation_invalid_type_raises_valueerror(self):
        """Test that invalid regulation type raises ValueError."""
        # Create a mock invalid regulation type
        class InvalidRegType:
            pass

        invalid_type = InvalidRegType()
        with pytest.raises(ValueError, match="not found in registry"):
            get_regulation(invalid_type)


class TestRegulationRegistry:
    """Test REGULATION_REGISTRY completeness."""

    def test_registry_contains_all_regulations(self):
        """Test that registry contains all 8 regulations."""
        assert len(REGULATION_REGISTRY) == 8

        # Verify all expected types are present
        assert RegulationType.EU_AI_ACT in REGULATION_REGISTRY
        assert RegulationType.GDPR in REGULATION_REGISTRY
        assert RegulationType.NIST_AI_RMF in REGULATION_REGISTRY
        assert RegulationType.US_EO_14110 in REGULATION_REGISTRY
        assert RegulationType.BRAZIL_LGPD in REGULATION_REGISTRY
        assert RegulationType.ISO_27001 in REGULATION_REGISTRY
        assert RegulationType.SOC2_TYPE_II in REGULATION_REGISTRY
        assert RegulationType.IEEE_7000 in REGULATION_REGISTRY

    def test_registry_values_are_correct_types(self):
        """Test that all registry values are Regulation objects."""
        from compliance.base import Regulation

        for reg_type, regulation in REGULATION_REGISTRY.items():
            assert isinstance(regulation, Regulation)
            assert regulation.regulation_type == reg_type


class TestRegulationDefinitions:
    """Test individual regulation definitions are complete."""

    def test_eu_ai_act_definition(self):
        """Test EU AI Act has all required fields."""
        assert EU_AI_ACT.regulation_type == RegulationType.EU_AI_ACT
        assert EU_AI_ACT.version == "1.0"
        assert isinstance(EU_AI_ACT.effective_date, datetime)
        assert len(EU_AI_ACT.controls) == 8
        assert EU_AI_ACT.url.startswith("https://")
        assert len(EU_AI_ACT.penalties) > 0

    def test_gdpr_definition(self):
        """Test GDPR has all required fields."""
        assert GDPR.regulation_type == RegulationType.GDPR
        assert GDPR.version == "2016/679"
        assert isinstance(GDPR.effective_date, datetime)
        assert GDPR.effective_date.year == 2018
        assert len(GDPR.controls) == 5
        assert "20 million" in GDPR.penalties

    def test_nist_ai_rmf_definition(self):
        """Test NIST AI RMF has all required fields."""
        assert NIST_AI_RMF.regulation_type == RegulationType.NIST_AI_RMF
        assert NIST_AI_RMF.version == "1.0"
        assert isinstance(NIST_AI_RMF.effective_date, datetime)
        assert len(NIST_AI_RMF.controls) == 7
        assert "voluntary" in NIST_AI_RMF.penalties.lower()

    def test_us_eo_14110_definition(self):
        """Test US EO 14110 has all required fields."""
        assert US_EO_14110.regulation_type == RegulationType.US_EO_14110
        assert US_EO_14110.version == "2023"
        assert isinstance(US_EO_14110.effective_date, datetime)
        assert US_EO_14110.effective_date.year == 2023
        assert len(US_EO_14110.controls) == 4

    def test_brazil_lgpd_definition(self):
        """Test Brazil LGPD has all required fields."""
        assert BRAZIL_LGPD.regulation_type == RegulationType.BRAZIL_LGPD
        assert "Lei nº 13.709/2018" in BRAZIL_LGPD.version
        assert isinstance(BRAZIL_LGPD.effective_date, datetime)
        assert BRAZIL_LGPD.effective_date.year == 2020
        assert len(BRAZIL_LGPD.controls) == 5
        assert "R$" in BRAZIL_LGPD.penalties

    def test_iso_27001_definition(self):
        """Test ISO 27001 has all required fields."""
        assert ISO_27001.regulation_type == RegulationType.ISO_27001
        assert ISO_27001.version == "2022"
        assert isinstance(ISO_27001.effective_date, datetime)
        assert ISO_27001.effective_date.year == 2022
        assert len(ISO_27001.controls) == 7
        assert "N/A" in ISO_27001.penalties

    def test_soc2_type_ii_definition(self):
        """Test SOC2 Type II has all required fields."""
        assert SOC2_TYPE_II.regulation_type == RegulationType.SOC2_TYPE_II
        assert SOC2_TYPE_II.version == "2017"
        assert isinstance(SOC2_TYPE_II.effective_date, datetime)
        assert len(SOC2_TYPE_II.controls) == 6
        assert "AICPA" in SOC2_TYPE_II.authority

    def test_ieee_7000_definition(self):
        """Test IEEE 7000 has all required fields."""
        assert IEEE_7000.regulation_type == RegulationType.IEEE_7000
        assert IEEE_7000.version == "2021"
        assert isinstance(IEEE_7000.effective_date, datetime)
        assert IEEE_7000.effective_date.year == 2021
        assert len(IEEE_7000.controls) == 6
        assert "ethical" in IEEE_7000.description.lower()


class TestRegulationControls:
    """Test that controls are properly defined."""

    def test_all_regulations_have_controls(self):
        """Test that all regulations have at least one control."""
        for regulation in REGULATION_REGISTRY.values():
            assert len(regulation.controls) > 0

    def test_controls_have_required_fields(self):
        """Test that all controls have required fields."""
        from compliance.base import Control

        # Check first control of each regulation
        for regulation in REGULATION_REGISTRY.values():
            control = regulation.controls[0]
            assert isinstance(control, Control)
            assert len(control.control_id) > 0
            assert control.regulation_type == regulation.regulation_type
            assert len(control.title) > 0
            assert len(control.description) > 0
            assert isinstance(control.mandatory, bool)
            assert len(control.evidence_required) > 0

    def test_mandatory_controls_exist(self):
        """Test that each regulation has mandatory controls."""
        for regulation in REGULATION_REGISTRY.values():
            mandatory_controls = [c for c in regulation.controls if c.mandatory]
            assert len(mandatory_controls) > 0, f"{regulation.name} has no mandatory controls"
