"""Introduction
Intel(R) Power Gadget is a software-based power estimation tool enabled for 2nd Generation Intel(R) Core(TM) processors or later. It includes a application, driver, and libraries to monitor and estimate real-time processor package power information in watts using the energy counters in the processor

Uninstall
To uninstall Intel(R) Power Gadget and all its components, run Uninstaller.pkg.

PowerLog
Intel(R) Power Gadget data can be logged from the command line (without running the GUI app) using PowerLog
Usage:
log power data to logfile for a period of time:
	PowerLog [-resolution ] -duration  [-verbose] [-file ]
start a command and log power data to logfile until the command finish
	PowerLog [-resolution ] [-file ] [-verbose] -cmd
Default for resolution = 50 ms
Default for logfile = PowerLog.ipg
-cmd must be the last parameter
API
The Intel(R) Power Gadget API is a framework (IntelPowerGadget.framework) that provides a C interface for reading current estimated processor power, current processor frequency, base frequency, thermal design power (TDP), current temperature, maximum temperature, timestamps, and elapsed time. It also provides logging functionality.

To use the API you'll need the Intel(R) Power Gadget for Mac driver and framework. These are included in the Intel(R) Power Gadget installer, or as a standalone API installer. The driver is installed to /Library/Extensions/EnergyDriver.kext, and the framework is installed to /Library/Frameworks/IntelPowerGadget.framework. See the API specification in /Library/Frameworks/IntelPowerGadget.framework/Headers/EnergyLib.h (C version) or /Library/Frameworks/IntelPowerGadget.framework/Headers/IntelPowerGadgetLib.h (C++ version)

To link with the Intel(R) Power Gadget API you simply need to include -framework IntelPowerGadget in your link command.

For more information, see Using the Intel Power Gadget API on Mac OS X.

Processor Energy (Total energy of the processor) = IA Energy + GT Energy (if applicable) + Others (not measured)
IA Energy (Energy of the CPU/processor cores)
GT Energy (Energy of the processor graphics) – If applicable , some processors for desktops and servers don’t have it or may have use discrete graphics"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

from PyPowerGadget.settings import *
import subprocess
import re


def parse_power_log():
    results = {
        TOTAL_TIME: 0,
        TOTAL_ENERGY_ALL: 0,
        TOTAL_ENERGY_CPU: 0,
        TOTAL_ENERGY_MEMORY: 0,
    }
    with open("test.csv") as f:
        content = f.read()
    results[TOTAL_TIME] = float(
        re.search('(?<=Total Elapsed Time \(sec\) = )(.*)(?=")', content).group(0)
    )
    results[TOTAL_ENERGY_ALL] = float(
        re.search(
            '(?<=Cumulative Package Energy_0 \(mWh\) = )(.*)(?=")', content
        ).group(0)
    )
    results[TOTAL_ENERGY_CPU] = float(
        re.search('(?<=Cumulative IA Energy_0 \(mWh\) = )(.*)(?=")', content).group(0)
    )
    results[TOTAL_ENERGY_MEMORY] = float(
        re.search('(?<=Cumulative DRAM Energy_0 \(mWh\) = )(.*)(?=")', content).group(0)
    )
    return results


def get_power_consumption(duration=1, resolution=500):
	out = subprocess.run(
	    [
	        POWERLOG_PATH_WIN,
	        "-resolution",
	        str(resolution),
	        "-duration",
	        str(duration),
	        "-file",
	        "test.csv",
	    ],
	    #stdout=open(os.devnull, "wb"),
	)
	print(out)
	logs = parse_power_log()
	return logs


if __name__ == "__main__":
    print(get_power_consumption())
