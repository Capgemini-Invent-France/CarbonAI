"""
tests for the Python class PowerGadget
"""
from pathlib import Path

import pytest

# from carbonai import PowerGadget
from carbonai.power_gadget import PowerGadget
from carbonai.utils import (
    TOTAL_CPU_TIME,
    TOTAL_ENERGY_ALL,
    TOTAL_ENERGY_CPU,
    TOTAL_ENERGY_MEMORY,
)


@pytest.fixture
def data():
    return Path.cwd() / "tests/data/test_intel_power_log.csv"


def test_parse_log(data):
    """
    Make sure parse_log indeed extract relevant information.
    """
    results = PowerGadget.parse_log(data)
    assert round(results[TOTAL_CPU_TIME], 2) == 2.02
    assert round(results[TOTAL_ENERGY_ALL], 2) == 1.38
    assert round(results[TOTAL_ENERGY_CPU], 2) == 1.05
    assert round(results[TOTAL_ENERGY_MEMORY], 2) == 0.38
