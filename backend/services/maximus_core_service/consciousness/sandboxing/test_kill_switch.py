"""
Tests for Kill Switch
"""
import pytest
from consciousness.sandboxing.kill_switch import KillSwitch, TriggerType


def test_kill_switch_initialization():
    """Test kill switch creation"""
    switch = KillSwitch()
    
    assert switch.armed == True
    assert len(switch.triggers) == 0
    assert len(switch.activation_history) == 0


def test_manual_activation():
    """Test manual kill switch activation"""
    switch = KillSwitch()
    
    activated = switch.activate(
        reason="Test activation",
        trigger_type=TriggerType.MANUAL
    )
    
    assert activated == True
    assert len(switch.activation_history) == 1
    
    history = switch.activation_history[0]
    assert history["reason"] == "Test activation"
    assert history["trigger_type"] == "manual"


def test_disarmed_switch():
    """Test that disarmed switch cannot activate"""
    switch = KillSwitch()
    switch.disarm("test_authorization")
    
    activated = switch.activate("Should not work")
    
    assert activated == False
    assert len(switch.activation_history) == 1  # Only disarm event


def test_add_trigger():
    """Test adding auto-kill triggers"""
    switch = KillSwitch()
    
    def test_condition():
        return False  # Not triggered
    
    trigger = switch.add_trigger(
        name="test_trigger",
        trigger_type=TriggerType.RESOURCE_SPIKE,
        condition=test_condition,
        description="Test trigger"
    )
    
    assert trigger.name == "test_trigger"
    assert trigger.enabled == True
    assert len(switch.triggers) == 1


def test_trigger_evaluation():
    """Test auto-trigger evaluation"""
    switch = KillSwitch()
    
    # Trigger that fires
    def always_true():
        return True
    
    switch.add_trigger(
        name="always_fires",
        trigger_type=TriggerType.SAFETY_PROTOCOL,
        condition=always_true,
        description="Always fires"
    )
    
    # Check triggers
    fired = switch.check_triggers()
    
    assert fired is not None
    assert fired.name == "always_fires"
    assert fired.trigger_count == 1
    assert len(switch.activation_history) > 0


def test_multiple_triggers():
    """Test multiple trigger conditions"""
    switch = KillSwitch()
    
    trigger1_fired = False
    trigger2_fired = False
    
    def condition1():
        return trigger1_fired
    
    def condition2():
        return trigger2_fired
    
    switch.add_trigger("trigger1", TriggerType.ETHICAL_VIOLATION, condition1, "First trigger")
    switch.add_trigger("trigger2", TriggerType.CORRUPTION, condition2, "Second trigger")
    
    # No triggers fire
    fired = switch.check_triggers()
    assert fired is None
    
    # First trigger fires
    trigger1_fired = True
    switch.arm()  # Re-arm after any previous activation
    fired = switch.check_triggers()
    assert fired is not None
    assert fired.name == "trigger1"


def test_alert_callback():
    """Test alert callback is called"""
    alerts = []
    
    def alert_handler(alert_data):
        alerts.append(alert_data)
    
    switch = KillSwitch(alert_callback=alert_handler)
    switch.activate("Test alert")
    
    assert len(alerts) == 1
    assert alerts[0]["event"] == "kill_switch_activated"


def test_get_status():
    """Test getting kill switch status"""
    switch = KillSwitch()
    
    # Add some triggers
    switch.add_trigger("test1", TriggerType.TIMEOUT, lambda: False, "Test 1")
    switch.add_trigger("test2", TriggerType.RESOURCE_SPIKE, lambda: False, "Test 2")
    
    # Activate once
    switch.activate("Test")
    
    status = switch.get_status()
    
    assert status["armed"] == True
    assert status["triggers_count"] == 2
    assert status["activations_count"] == 1
    assert len(status["triggers"]) == 2
    assert len(status["recent_activations"]) == 1


def test_arm_disarm_cycle():
    """Test arming and disarming"""
    switch = KillSwitch()
    
    assert switch.armed == True
    
    switch.disarm("test_auth")
    assert switch.armed == False
    
    switch.arm()
    assert switch.armed == True


def test_disabled_trigger():
    """Test that disabled triggers don't fire"""
    switch = KillSwitch()
    
    def always_true():
        return True
    
    trigger = switch.add_trigger(
        "disabled_test",
        TriggerType.SAFETY_PROTOCOL,
        always_true,
        "Should not fire"
    )
    
    # Disable trigger
    trigger.enabled = False
    
    # Check triggers
    fired = switch.check_triggers()
    
    # Should not fire because disabled
    assert fired is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
