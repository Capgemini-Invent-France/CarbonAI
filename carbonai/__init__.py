"""
    This package allows you to measure the power drained by your
    computer or server during the execution of a function
"""
__all__ = ["PowerMeter", "MagicPowerMeter"]

from .magic_power_meter import MagicPowerMeter
from .power_meter import PowerMeter
