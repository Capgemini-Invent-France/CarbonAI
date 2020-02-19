"""
Introduction
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
GT Energy (Energy of the processor graphics) – If applicable , some processors for desktops and servers don’t have it or may have use discrete graphics
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

from PyPowerGadget.settings import *
import subprocess
import re

import pandas as pd
import time
import multiprocessing
from multiprocessing import Process, Manager


class PowerGadget:
    def __init__(self):
        self.log_file = (
            Path(os.path.dirname(os.path.abspath(__file__))) / INTELPOWERLOG_FILENAME
        )
        self.recorded_power = []

    def parse_power_log(self):
        results = {
            TOTAL_TIME: 0,
            TOTAL_ENERGY_ALL: 0,
            TOTAL_ENERGY_CPU: 0,
            TOTAL_ENERGY_MEMORY: 0,
        }
        content = self.log_file.read_text()

        results[TOTAL_TIME] = float(
            re.search('(?<=Total Elapsed Time \(sec\) = )(.*)(?=")', content).group(0)
        )
        results[TOTAL_ENERGY_ALL] = float(
            re.search(
                '(?<=Cumulative Package Energy_0 \(mWh\) = )(.*)(?=")', content
            ).group(0)
        )
        results[TOTAL_ENERGY_CPU] = float(
            re.search('(?<=Cumulative IA Energy_0 \(mWh\) = )(.*)(?=")', content).group(
                0
            )
        )
        results[TOTAL_ENERGY_MEMORY] = float(
            re.search(
                '(?<=Cumulative DRAM Energy_0 \(mWh\) = )(.*)(?=")', content
            ).group(0)
        )
        return results


class PowerGadgetMac(PowerGadget):
    def __init__(self, power_log_path=""):
        super().__init__()
        if len(power_log_path) > 0:
            self.power_log_path = Path(power_log_path)
        else:
            self.power_log_path = POWERLOG_PATH_MAC

        if not self.power_log_path.exists():
            raise ModuleNotFoundError(
                "We didn't find the Intel Power Gadget tool. \nMake sure it is installed (download available here : https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg).\nIf it is installed, we looked for it here:"
                + str(self.power_log_path)
                + ", try passing the path to the powerLog tool to the powerMeter."
            )

    def get_power_consumption(self, duration=1, resolution=500):
        out = subprocess.run(
            [
                self.power_log_path,
                "-resolution",
                str(resolution),
                "-duration",
                str(duration),
                "-file",
                self.log_file,
            ],
            stdout=open(os.devnull, "wb"),
        )
        consumption = self.parse_power_log()
        return consumption

    def extract_power(self, list_of_power, interval=1):
        list_of_power.append(self.get_power_consumption(duration=interval))
        while True:
            list_of_power.append(self.get_power_consumption(duration=interval))

    def execute_function(self, fun, fun_args, results):
        results["results"] = fun(*fun_args[0], **fun_args[1])

    def wrapper(self, func, *args, time_interval=1, **kwargs):
        multiprocessing.set_start_method("spawn", force=True)
        with Manager() as manager:
            power_draws = manager.list()
            return_dict = manager.dict()

            func_process = Process(
                target=self.execute_function, args=(func, (args, kwargs), return_dict)
            )
            power_process = Process(
                target=self.extract_power, args=(power_draws, time_interval)
            )
            print("starting CPU power monitoring ...")

            power_process.start()
            func_process.start()

            func_process.join()
            power_process.terminate()
            power_process.join()
            print("stoping CPU power monitoring ...")

            power_draws_list = list(power_draws)
            time.sleep(2)
            power_draws_list.append(self.parse_power_log())
            results = return_dict["results"]
        self.recorded_power = pd.DataFrame.from_records(power_draws_list)
        self.recorded_power = self.recorded_power.sum(axis=0)
        return results


class PowerGadgetWin(PowerGadget):
    def __init__(self, power_log_path=""):
        super().__init__()
        if len(power_log_path) > 0:
            self.power_log_path = Path(power_log_path)
        else:
            self.power_log_path = POWERLOG_PATH_WIN

        if not self.power_log_path.exists():
            raise ModuleNotFoundError(
                "We didn't find the Intel Power Gadget tool. \nMake sure it is installed (download available here : https://software.intel.com/file/823776/download).\nIf it is installed, we looked for it here:"
                + str(self.power_log_path)
                + ", try passing the path to the powerLog tool to the powerMeter."
            )

    def wrapper(self, func, *args, time_interval=1, **kwargs):
        print("starting CPU power monitoring ...")
        out = subprocess.run(
            ["start", self.power_log_path, "/min"], stdout=open(os.devnull, "wb")
        )
        out = subprocess.run(
            [self.power_log_path, "-start"], stdout=open(os.devnull, "wb")
        )
        results = func(*args, **kwargs)
        print("stoping CPU power monitoring ...")
        out = subprocess.run(
            [self.power_log_path, "-stop"], stdout=open(os.devnull, "wb")
        )
        self.recorded_power = self.parse_power_log()
        return results


class PowerGadgetLinux(PowerGadget):
    def __init__(self, power_log_path=""):
        super().__init__()
        # if len(power_log_path) > 0:
        #     self.power_log_path = Path(power_log_path)
        # else:
        #     self.power_log_path = POWERLOG_PATH_WIN
        #
        # if not self.power_log_path.exists():
        #     raise ModuleNotFoundError(
        #         "We didn't find the Intel Power Gadget tool. \nMake sure it is installed (download available here : https://software.intel.com/file/823776/download).\nIf it is installed, we looked for it here:"
        #         + str(self.power_log_path)
        #         + ", try passing the path to the powerLog tool to the powerMeter."
        #     )

    def wrapper(self, func, *args, time_interval=1, **kwargs):
        print("starting CPU power monitoring ...")

        # out = subprocess.run(
        #     ["start", self.power_log_path, "/min"], stdout=open(os.devnull, "wb")
        # )
        # out = subprocess.run(
        #     [self.power_log_path, "-start"], stdout=open(os.devnull, "wb")
        # )
        results = func(*args, **kwargs)
        # out = subprocess.run(
        #     [self.power_log_path, "-stop"], stdout=open(os.devnull, "wb")
        # )
        print("stoping CPU power monitoring ...")

        self.recorded_power = self.parse_power_log()
        return results


if __name__ == "__main__":
    print(get_power_consumption())
