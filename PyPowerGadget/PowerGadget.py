#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import glob

import pandas as pd
import struct
import time
import multiprocessing
from multiprocessing import Process, Manager


class PowerGadget:
    def __init__(self):
        self.recorded_power = []

    def parse_power_log(self, log_file):
        content = log_file.read_text()
        if not "Total Elapsed Time" in content:
            time.sleep(2)
            content = log_file.read_text()
        results = {
            TOTAL_CPU_TIME: 0,
            TOTAL_ENERGY_ALL: 0,
            TOTAL_ENERGY_CPU: 0,
            TOTAL_ENERGY_MEMORY: 0,
        }

        results[TOTAL_CPU_TIME] = float(
            re.search("(?<=Total Elapsed Time \(sec\) = )(\d|\.)*", content).group(0)
        )
        results[TOTAL_ENERGY_ALL] = float(
            re.search(
                "((?<=Cumulative Package Energy_0 \(mWh\) = )|(?<=Cumulative Processor Energy_0 \(mWh\) = ))(\d|\.)*",
                content,
            ).group(0)
        )
        results[TOTAL_ENERGY_CPU] = float(
            re.search("(?<=Cumulative IA Energy_0 \(mWh\) = )(\d|\.)*", content).group(
                0
            )
        )
        results[TOTAL_ENERGY_MEMORY] = float(
            re.search(
                "(?<=Cumulative DRAM Energy_0 \(mWh\) = )(\d|\.)*", content
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
        self.log_file = self.__get_log_file()

    def __get_log_file(self):
        return PACKAGE_PATH / MAC_INTELPOWERLOG_FILENAME

    def __get_power_consumption(self, duration=1, resolution=500):
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
        consumption = self.parse_power_log(self.log_file)
        return consumption

    def extract_power(self, list_of_power, interval=1):
        list_of_power.append(self.__get_power_consumption(duration=interval))
        while True:
            list_of_power.append(self.__get_power_consumption(duration=interval))

    def execute_function(self, fun, fun_args, results):
        results["results"] = fun(*fun_args[0], **fun_args[1])

    def wrapper(self, func, *args, time_interval=1, **kwargs):
        multiprocessing.set_start_method("spawn", force=True)
        with Manager() as manager:
            power_draws = manager.list()
            return_dict = manager.dict()
            return_dict["results"] = None
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
            power_draws_list.append(self.parse_power_log(self.log_file))
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
            self.power_log_path = POWERLOG_PATH_WIN / POWERLOG_TOOL_WIN
        if not self.power_log_path.exists():
            raise ModuleNotFoundError(
                "We didn't find the Intel Power Gadget tool. \nMake sure it is installed (download available here : https://software.intel.com/file/823776/download).\nIf it is installed, we looked for it here:"
                + str(self.power_log_path)
                + ", try passing the path to the powerLog tool to the powerMeter."
            )

    def wrapper(self, func, *args, time_interval=1, **kwargs):
        print("starting CPU power monitoring ...")
        out = subprocess.Popen(
            '"' + str(self.power_log_path) + '" /min',
            stdin=None,
            stdout=None,
            stderr=None,
            shell=True,
        )
        time.sleep(1)
        print("start logging")
        out = subprocess.run('"' + str(self.power_log_path) + '" -start', shell=True)
        results = func(*args, **kwargs)
        print("stoping CPU power monitoring ...")
        out = subprocess.run('"' + str(self.power_log_path) + '" -stop', shell=True)
        out = subprocess.run(
            'taskkill /IM "' + POWERLOG_TOOL_WIN + '"',
            stdout=open(os.devnull, "wb"),
            shell=True,
        )
        log_file = self.__get_log_file()
        self.recorded_power = self.parse_power_log(log_file)
        os.remove(log_file)
        return results

    def __get_log_file(self):
        file_names = glob.glob(str(HOME_DIR / "Documents" / WIN_INTELPOWERLOG_FILENAME))
        file_names.sort(key=lambda f: list(map(int, re.split("-|_|\.|/", f)[-7:-1])))
        return Path(file_names[-1])


class PowerGadgetLinux(PowerGadget):
    def __init__(self, power_log_path=""):
        super().__init__()

        # the user needs to execute as root
        if os.geteuid() != 0:
            raise PermissionError("You need to execute this program as root")

        self.cpu_ids = self.__get_cpu_ids()
        self.MSR_RAPL_POWER_UNIT = 0x606
        self.MSR_PKG_RAPL_POWER_LIMIT = 0x610
        self.MSR_PKG_ENERGY_STATUS = 0x611  #  reports measured actual energy usage
        self.MSR_DRAM_ENERGY_STATUS = 0x619
        self.MSR_PKG_PERF_STATUS = 0x613
        self.MSR_PKG_POWER_INFO = 0x614
        self.MSR_PP0_ENERGY_STATUS = 0x639

    def __get_cpu_ids(self):
        """
        Returns the cpu id of this machine
        """
        api_file = open("/sys/devices/system/cpu/present", "r")

        cpu_id_tmp = re.findall("\d+|-", api_file.readline().strip())
        cpu_id_list = []
        for i in range(len(cpu_id_tmp)):
            if cpu_id_tmp[i] == "-":
                for cpu_id in range(int(cpu_id_tmp[i - 1]) + 1, int(cpu_id_tmp[i + 1])):
                    cpu_id_list.append(int(cpu_id))
            else:
                cpu_id_list.append(int(cpu_id_tmp[i]))
        return cpu_id_list

        os.lseek(fd, msr, os.SEEK_SET)
        return struct.unpack("Q", os.read(fd, 8))[0]

    def __read_msr(self, fd, msr):
        os.lseek(fd, msr, os.SEEK_SET)
        return struct.unpack("Q", os.read(fd, 8))[0]

    def __get_used_units(self, cpu):
        fd = os.open("/dev/cpu/%d/msr" % (cpu,), os.O_RDONLY)
        # Calculate the units used
        result = self.__read_msr(fd, self.MSR_RAPL_POWER_UNIT)
        power_units = 0.5 ** (result & 0xF)
        cpu_energy_units = 0.5 ** ((result >> 8) & 0x1F)
        dram_energy_units = cpu_energy_units
        time_units = 0.5 ** ((result >> 16) & 0xF)
        os.close(fd)
        return power_units, cpu_energy_units, dram_energy_units, time_units

    def __get_cpu_energy(self, cpu, unit):
        fd = os.open("/dev/cpu/%d/msr" % (cpu,), os.O_RDONLY)
        result = self.__read_msr(fd, self.MSR_PKG_ENERGY_STATUS)
        os.close(fd)
        return result * unit / 3.6

    def __get_dram_energy(self, cpu, unit):
        fd = os.open("/dev/cpu/%d/msr" % (cpu,), os.O_RDONLY)
        result = self.__read_msr(fd, self.MSR_DRAM_ENERGY_STATUS)
        os.close(fd)
        return result * unit / 3.6

    def extract_power(self, power_draws, interval=1):
        power_draws[TOTAL_CPU_TIME] = 0
        power_draws[TOTAL_ENERGY_CPU] = 0
        power_draws[TOTAL_ENERGY_MEMORY] = 0
        prev_dram_energies = []
        prev_cpu_energies = []
        for cpu in self.cpu_ids:
            power_units, cpu_energy_units, dram_energy_units, time_units = self.__get_used_units(
                cpu
            )
            prev_dram_energies.append(self.__get_dram_energy(cpu, dram_energy_units))
            prev_cpu_energies.append(self.__get_cpu_energy(cpu, cpu_energy_units))
        t0 = time.time()
        while True:
            time.sleep(interval)
            for i, cpu in enumerate(self.cpu_ids):
                power_units, cpu_energy_units, dram_energy_units, time_units = self.__get_used_units(
                    cpu
                )
                current_dram_energy = self.__get_dram_energy(cpu, dram_energy_units)
                current_cpu_energy = self.__get_cpu_energy(cpu, cpu_energy_units)
                if prev_cpu_energies > cpu_energy_units:
                    cpu_energy_units *= 2
                if prev_dram_energies > dram_energy_units:
                    dram_energy_units *= 2
                power_draws[TOTAL_ENERGY_CPU] += (
                    current_cpu_energy - prev_cpu_energies[i]
                )
                power_draws[TOTAL_ENERGY_MEMORY] += (
                    current_dram_energy - prev_dram_energies[i]
                )
                prev_cpu_energies[i] = current_cpu_energy
                prev_dram_energies[i] = current_dram_energy
            t1 = time.time()
            power_draws[TOTAL_CPU_TIME] += t1 - t0
            t0 = t1

    def execute_function(self, fun, fun_args, results):
        results["results"] = fun(*fun_args[0], **fun_args[1])

    def wrapper(self, func, *args, time_interval=1, **kwargs):
        multiprocessing.set_start_method("spawn", force=True)
        with Manager() as manager:
            power_draws = manager.dict()
            return_dict = manager.dict()
            return_dict["results"] = None
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
            results = return_dict["results"]
            self.recorded_power = dict(power_draws)
            self.recorded_power[TOTAL_ENERGY_ALL] = None
        return results


if __name__ == "__main__":
    print(get_power_consumption())
