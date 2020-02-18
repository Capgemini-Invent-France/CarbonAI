import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

from PyPowerGadget.PowerMeter import *
from PyPowerGadget.settings import *


def say_whee():
    import time

    time.sleep(11)
    print("Whee!")
    return


if __name__ == "__main__":
    power_meter = PowerMeter()
    print(power_meter.mesure_power(say_whee)())
