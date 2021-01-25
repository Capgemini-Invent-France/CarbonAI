"""
tests for the Python class PowerMeter
"""
import pytest
from pathlib import Path

from PyPowerGadget.PowerMeter import PowerMeter

@pytest.fixture
def data():
    return Path.cwd() / 'tests/data/config.json'

def test_from_config(data):
    """
    Make sure the class method from_config works.
    """
    power_meter = PowerMeter.from_config(data)
    assert power_meter.project == "Project Test"
    assert power_meter.user == "customUsernameTest"