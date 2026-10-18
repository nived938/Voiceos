import pytest
from ai.tools import calculate, get_current_time, system_status

def test_calculate_valid():
    assert calculate("2 + 2") == "4"
    assert calculate("10 * 5.5") == "55.0"
    assert calculate("(100 - 20) / 2") == "40.0"

def test_calculate_security():
    # Dangerous expressions should be refused
    res = calculate("__import__('os').system('dir')")
    assert "unsupported characters" in res or "Error" in res

def test_get_current_time():
    t = get_current_time()
    assert len(t) > 5
    assert any(day in t for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

def test_system_status():
    stat = system_status()
    assert "cpu_usage_pct" in stat
    assert "memory_used_gb" in stat
    assert "os" in stat
