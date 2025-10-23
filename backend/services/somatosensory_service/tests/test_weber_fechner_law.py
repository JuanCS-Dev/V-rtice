"""
Unit tests for Somatosensory Service - weber_fechner_law.py

Target: 100% coverage
Testing: Weber-Fechner Law (perceived intensity calculation)
"""

import sys
from pathlib import Path

service_dir = Path(__file__).parent.parent
sys.path.insert(0, str(service_dir))

import pytest
import math


# ====== INITIALIZATION TESTS ======

def test_weber_fechner_law_init_default():
    """Test WeberFechnerLaw initialization with default k_constant."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()
    assert wfl.k_constant == 0.1


def test_weber_fechner_law_init_custom():
    """Test WeberFechnerLaw initialization with custom k_constant."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.5)
    assert wfl.k_constant == 0.5


# ====== CALCULATE_PERCEIVED_INTENSITY TESTS ======

def test_calculate_perceived_intensity_basic():
    """Test basic perceived intensity calculation."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)

    # P = k * log(S / S0) = 0.1 * log(10 / 1) = 0.1 * log(10)
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=10.0, reference_stimulus=1.0)
    expected = 0.1 * math.log(10.0)
    assert result == pytest.approx(expected)


def test_calculate_perceived_intensity_default_reference():
    """Test perceived intensity calculation with default reference."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.2)

    # Default reference is 1.0
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=5.0)
    expected = 0.2 * math.log(5.0)
    assert result == pytest.approx(expected)


def test_calculate_perceived_intensity_equal_stimuli():
    """Test perceived intensity when stimulus equals reference (log(1) = 0)."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.3)

    # P = 0.3 * log(5 / 5) = 0.3 * log(1) = 0.3 * 0 = 0
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=5.0, reference_stimulus=5.0)
    assert result == pytest.approx(0.0)


def test_calculate_perceived_intensity_high_k():
    """Test perceived intensity with high Weber constant."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=1.0)

    # P = 1.0 * log(100 / 1) = log(100)
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=100.0, reference_stimulus=1.0)
    expected = math.log(100.0)
    assert result == pytest.approx(expected)


def test_calculate_perceived_intensity_fractional_stimulus():
    """Test perceived intensity with stimulus less than reference."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)

    # P = 0.1 * log(0.5 / 1.0) = 0.1 * log(0.5) = negative value
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=0.5, reference_stimulus=1.0)
    expected = 0.1 * math.log(0.5)
    assert result == pytest.approx(expected)
    assert result < 0  # Should be negative


def test_calculate_perceived_intensity_zero_stimulus_error():
    """Test ValueError when stimulus magnitude is zero."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()

    with pytest.raises(ValueError, match="Stimulus magnitudes must be positive"):
        wfl.calculate_perceived_intensity(stimulus_magnitude=0.0, reference_stimulus=1.0)


def test_calculate_perceived_intensity_negative_stimulus_error():
    """Test ValueError when stimulus magnitude is negative."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()

    with pytest.raises(ValueError, match="Stimulus magnitudes must be positive"):
        wfl.calculate_perceived_intensity(stimulus_magnitude=-5.0, reference_stimulus=1.0)


def test_calculate_perceived_intensity_zero_reference_error():
    """Test ValueError when reference stimulus is zero."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()

    with pytest.raises(ValueError, match="Stimulus magnitudes must be positive"):
        wfl.calculate_perceived_intensity(stimulus_magnitude=10.0, reference_stimulus=0.0)


def test_calculate_perceived_intensity_negative_reference_error():
    """Test ValueError when reference stimulus is negative."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()

    with pytest.raises(ValueError, match="Stimulus magnitudes must be positive"):
        wfl.calculate_perceived_intensity(stimulus_magnitude=10.0, reference_stimulus=-1.0)


# ====== GET_K_CONSTANT TESTS ======

def test_get_k_constant():
    """Test get_k_constant returns correct value."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.25)
    assert wfl.get_k_constant() == 0.25


# ====== SET_K_CONSTANT TESTS ======

def test_set_k_constant_valid():
    """Test setting a valid k_constant."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)
    wfl.set_k_constant(0.5)
    assert wfl.k_constant == 0.5
    assert wfl.get_k_constant() == 0.5


def test_set_k_constant_affects_calculation():
    """Test that changing k_constant affects subsequent calculations."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)

    result1 = wfl.calculate_perceived_intensity(stimulus_magnitude=10.0)
    expected1 = 0.1 * math.log(10.0)
    assert result1 == pytest.approx(expected1)

    # Change k_constant
    wfl.set_k_constant(0.5)

    result2 = wfl.calculate_perceived_intensity(stimulus_magnitude=10.0)
    expected2 = 0.5 * math.log(10.0)
    assert result2 == pytest.approx(expected2)
    assert result2 != result1


def test_set_k_constant_zero_error():
    """Test ValueError when setting k_constant to zero."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()

    with pytest.raises(ValueError, match="Weber constant \\(k\\) must be positive"):
        wfl.set_k_constant(0.0)


def test_set_k_constant_negative_error():
    """Test ValueError when setting k_constant to negative."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw()

    with pytest.raises(ValueError, match="Weber constant \\(k\\) must be positive"):
        wfl.set_k_constant(-0.5)


# ====== EDGE CASES ======

def test_very_small_stimulus():
    """Test perceived intensity with very small stimulus."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)

    # Very small stimulus close to reference
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=1.001, reference_stimulus=1.0)
    expected = 0.1 * math.log(1.001)
    assert result == pytest.approx(expected)
    assert result > 0  # Should be slightly positive


def test_very_large_stimulus():
    """Test perceived intensity with very large stimulus."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)

    # Very large stimulus
    result = wfl.calculate_perceived_intensity(stimulus_magnitude=10000.0, reference_stimulus=1.0)
    expected = 0.1 * math.log(10000.0)
    assert result == pytest.approx(expected)


def test_very_small_k_constant():
    """Test perceived intensity with very small k_constant."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.001)

    result = wfl.calculate_perceived_intensity(stimulus_magnitude=10.0, reference_stimulus=1.0)
    expected = 0.001 * math.log(10.0)
    assert result == pytest.approx(expected)
    assert result < 0.01  # Should be very small


def test_various_stimulus_ratios():
    """Test perceived intensity with various stimulus/reference ratios."""
    from weber_fechner_law import WeberFechnerLaw

    wfl = WeberFechnerLaw(k_constant=0.1)

    # Test doubling
    result_double = wfl.calculate_perceived_intensity(stimulus_magnitude=2.0, reference_stimulus=1.0)
    assert result_double == pytest.approx(0.1 * math.log(2.0))

    # Test tripling
    result_triple = wfl.calculate_perceived_intensity(stimulus_magnitude=3.0, reference_stimulus=1.0)
    assert result_triple == pytest.approx(0.1 * math.log(3.0))

    # Test 10x increase
    result_10x = wfl.calculate_perceived_intensity(stimulus_magnitude=10.0, reference_stimulus=1.0)
    assert result_10x == pytest.approx(0.1 * math.log(10.0))


"""
COVERAGE SUMMARY:

Covered (100%):
✅ WeberFechnerLaw.__init__() - default and custom k_constant
✅ calculate_perceived_intensity() - all scenarios (basic, equal, high k, fractional)
✅ calculate_perceived_intensity() - ValueError validations (zero/negative stimulus/reference)
✅ get_k_constant()
✅ set_k_constant() - valid values and effect on calculations
✅ set_k_constant() - ValueError validations (zero/negative)
✅ Edge cases (very small/large stimuli, various ratios)

Total: 20 tests for weber_fechner_law.py
Execution: <0.5s
"""
