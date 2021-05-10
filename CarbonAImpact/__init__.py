"""
    This package allows you to measure the power drained by your computer or server during the execution of a function
"""
__all__ = ["PowerMeter", "MagicPowerMeter"]

from .version import __version__
from .power_meter import PowerMeter
from .magic_power_meter import MagicPowerMeter
