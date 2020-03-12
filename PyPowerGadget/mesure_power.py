import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

from PyPowerGadget.PowerMeter import *
from PyPowerGadget.settings import *
import time

power_meter = PowerMeter(project_name="Test mesure power")


@power_meter.mesure_power(algorithm="classic python", package="None")
def say_whee():

    # for i in range(11):
    time.sleep(31)
    print("Whee!")
    # raise "test"
    return


if __name__ == "__main__":
    print(say_whee())

    # a notebook like program
    power_meter.start_mesure(algorithm="classic python", package="None")
    time.sleep(11)
    print("Whee!")
    # raise "test"
    power_meter.stop_mesure()

    with power_meter(algorithm="classic python", package="None") as p_m:
        time.sleep(11)
        print("Whee!")
