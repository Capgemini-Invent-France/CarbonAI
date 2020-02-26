"""
    This package allows you to mesure the power drained by your computer or server during the execution of a function
"""

__version__ = "0.0.3"

from PyPowerGadget.PowerMeter import PowerMeter
from PyPowerGadget.functions import get_logged_data

__all__ = ["PowerMeter", "get_logged_data"]
