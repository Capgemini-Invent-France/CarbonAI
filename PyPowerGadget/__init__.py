"""
    This package allows you to measure the power drained by your computer or server during the execution of a function
"""

__version__ = "0.0.6dev"

from PyPowerGadget.PowerMeter import PowerMeter
from PyPowerGadget.functions import get_logged_data
from PyPowerGadget.MagicPowerMeter import MagicPowerMeter


__all__ = ["PowerMeter", "MagicPowerMeter", "get_logged_data"]
