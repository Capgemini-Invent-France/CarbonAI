"""
    This package allows you to measure the power drained by your computer or server during the execution of a function
"""
__all__ = ["PowerMeter", "MagicPowerMeter", "get_logged_data"]

from PyPowerGadget.version import __version__
from PyPowerGadget.PowerMeter import PowerMeter
from PyPowerGadget.utils import get_logged_data
from PyPowerGadget.MagicPowerMeter import MagicPowerMeter



