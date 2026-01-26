import pytest
from services.power_service import calculate_rig_power

def test_empty_rig_returns_none():
    assert calculate_rig_power({}) is None
    assert calculate_rig_power(None) is None

def test_manual_power_entries_only():
    rig = {
        "power_main": "1000",
        "power_light": "500"
    }
    result = calculate_rig_power(rig)
    assert result is not None
    assert result["total_power"] == 1500.0
    assert result["total_watt"] is None

def test_fixture_items_power():
    rig = {
        "spots_items": [
            {"count": "10", "watt": "200"}, # 2000W
            {"count": "5", "watt": "100"}   # 500W
        ],
        "washes_items": [
             {"count": "2", "watt": "300"}  # 600W
        ]
    }
    # Total: 3100 W
    result = calculate_rig_power(rig)
    assert result["total_watt"] == 3100.0
    assert result["total_kw"] == 3.1
    # Check calculated values approximately
    assert result["current_1ph"] > 0
    assert result["current_3ph"] > 0

def test_custom_devices_power():
    rig = {
        "custom_devices": [
            {"count": "2", "watt": "500"} # 1000W
        ]
    }
    result = calculate_rig_power(rig)
    assert result["total_watt"] == 1000.0
    assert result["total_kw"] == 1.0

def test_mixed_inputs_and_formatting():
    rig = {
        "spots_items": [
            {"count": " 10 ", "watt": "150,5"} # 1505W
        ],
        "power_main": "200,5"
    }
    # 10 * 150.5 = 1505.0
    result = calculate_rig_power(rig)
    assert result["total_watt"] == 1505.0
    assert result["total_power"] == 200.5

def test_invalid_values_are_handled_gracefully():
    rig = {
        "spots_items": [
            {"count": "abc", "watt": "xyz"} 
        ]
    }
    result = calculate_rig_power(rig)
    assert result is None
