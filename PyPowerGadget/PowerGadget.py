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
import threading


class PowerGadget:
    def __init__(self):
        self.recorded_power = []

    def parse_power_log(self, log_file):
        content = log_file.read_text()
        if not "Total Elapsed Time" in content:
            print("The log file does not seem to written yet, we'll wait 2 secs.")
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
        self.thread = None

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

    def extract_power(self, interval=1):
        self.power_draws.append(self.__get_power_consumption(duration=interval))
        while getattr(self.thread, "do_run", True):
            self.power_draws.append(self.__get_power_consumption(duration=interval))
        self.power_draws.append(self.__get_power_consumption(duration=interval))

    def execute_function(self, fun, fun_args, results):
        results["results"] = fun(*fun_args[0], **fun_args[1])

    def start_measure(self):
        print("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            self.stop_measure()
        self.power_draws = []
        self.thread = threading.Thread(target=self.extract_power, args=())
        self.thread.start()

    def stop_measure(self):
        print("stoping CPU power monitoring ...")
        self.thread.do_run = False
        self.thread.join()
        self.recorded_power = pd.DataFrame.from_records(self.power_draws)
        self.recorded_power = self.recorded_power.sum(axis=0)


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

    def start_measure(self, time_interval=1):
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

    def stop_measure(self):
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

    def __get_log_file(self):
        file_names = glob.glob(str(HOME_DIR / "Documents" / WIN_INTELPOWERLOG_FILENAME))
        file_names.sort(key=lambda f: list(map(int, re.split("-|_|\.|/", f)[-7:-1])))
        return Path(file_names[-1])


class PowerGadgetLinux(PowerGadget):
    def __init__(self):
        super().__init__()
        self.cpu_ids = self.__get_cpu_ids()

    def __get_cpu_ids(self):
        """
        Returns the cpu id of this machine
        """
        cpu_id_list = []
        for filename in glob.glob(CPU_IDS_DIR):
            with open(filename, "r") as f:
                package_id = int(f.read())
            if package_id not in cpu_id_list:
                cpu_id_list.append(package_id)
        return cpu_id_list


class PowerGadgetLinuxRAPL(PowerGadgetLinux):
    def __init__(self):
        super().__init__()
        self.dram_ids = self.__get_drams_ids()

    def __get_drams_ids(self):
        dram_id_list = []
        for cpu in self.cpu_ids:
            dram_paths = glob.glob(
                READ_RAPL_PATH.format(cpu)
                + RAPL_DRAM_PATH.format(cpu, "*")
                + RAPL_DEVICENAME_FILE
            )
            for i, dram_file in enumerate(dram_paths):
                dram_file = Path(dram_file)
                if "dram" in dram_file.read_text():
                    dram_id_list.append((cpu, i))
                    break
        return dram_id_list

    def collect_power_usage(self):
        for i, cpu_id in enumerate(self.cpu_ids):
            self.cpu_powers[i] = self.__get_cpu_energy(cpu_id) - self.cpu_powers[i]
        for i, (cpu_id, dram_id) in enumerate(self.dram_ids):
            self.dram_powers[i] = (
                self.__get_dram_energy(cpu_id, dram_id) - self.dram_powers[i]
            )

    def start_measure(self):
        print("starting CPU power monitoring ...")
        self.start_time = time.time()
        self.power_draws = []
        self.recorded_power = {}
        self.cpu_powers = []
        self.dram_powers = []
        for cpu_id in self.cpu_ids:
            self.cpu_powers.append(self.__get_cpu_energy(cpu_id))
        for cpu_id, dram_id in self.dram_ids:
            self.dram_powers.append(self.__get_dram_energy(cpu_id, dram_id))

    def stop_measure(self):
        print("stoping CPU power monitoring ...")
        self.collect_power_usage()
        self.recorded_power[TOTAL_ENERGY_CPU] = sum(self.cpu_powers) / 3600 / 1000
        self.recorded_power[TOTAL_ENERGY_MEMORY] = sum(self.dram_powers) / 3600 / 1000
        end_time = time.time()
        self.recorded_power[TOTAL_CPU_TIME] = end_time - self.start_time
        self.recorded_power[TOTAL_ENERGY_ALL] = 0

    def __get_cpu_energy(self, cpu):
        cpu_energy_file = Path(READ_RAPL_PATH.format(cpu)) / RAPL_ENERGY_FILE
        energy = int(cpu_energy_file.read_text())
        return energy

    def __get_dram_energy(self, cpu, dram):
        dram_energy_file = (
            Path(READ_RAPL_PATH.format(cpu))
            / (RAPL_DRAM_PATH.format(cpu, dram))
            / RAPL_ENERGY_FILE
        )
        energy = int(dram_energy_file.read_text())
        return energy


class PowerGadgetLinuxMSR(PowerGadgetLinux):
    def __init__(self):
        super().__init__()
        # the user needs to execute as root
        if os.geteuid() != 0:
            raise PermissionError("You need to execute this program as root")
        self.thread = None

        self.MSR_RAPL_POWER_UNIT = 0x606
        self.MSR_PKG_RAPL_POWER_LIMIT = 0x610
        self.MSR_PKG_ENERGY_STATUS = 0x611  #  reports measured actual energy usage
        self.MSR_DRAM_ENERGY_STATUS = 0x619
        self.MSR_PKG_PERF_STATUS = 0x613
        self.MSR_PKG_POWER_INFO = 0x614
        self.MSR_PP0_ENERGY_STATUS = 0x639

    def __read_msr(self, fd, msr):
        os.lseek(fd, msr, os.SEEK_SET)
        return struct.unpack("Q", os.read(fd, 8))[0]

    def __get_used_units(self, cpu):
        fd = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        # Calculate the units used
        result = self.__read_msr(fd, self.MSR_RAPL_POWER_UNIT)
        power_units = 0.5 ** (result & 0xF)
        cpu_energy_units = 0.5 ** ((result >> 8) & 0x1F)
        dram_energy_units = cpu_energy_units
        time_units = 0.5 ** ((result >> 16) & 0xF)
        os.close(fd)
        return power_units, cpu_energy_units, dram_energy_units, time_units

    def __get_cpu_energy(self, cpu, unit):
        fd = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        result = self.__read_msr(fd, self.MSR_PKG_ENERGY_STATUS)
        os.close(fd)
        return result * unit / 3.6

    def __get_dram_energy(self, cpu, unit):
        fd = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        result = self.__read_msr(fd, self.MSR_DRAM_ENERGY_STATUS)
        os.close(fd)
        return result * unit / 3.6

    def __get_computer_consomption(self, prev_cpu_energies, prev_dram_energies):
        cpu_power = 0
        dram_power = 0
        for i, cpu in enumerate(self.cpu_ids):
            _, cpu_energy_units, dram_energy_units, _ = self.__get_used_units(cpu)
            current_dram_energy = self.__get_dram_energy(cpu, dram_energy_units)
            current_cpu_energy = self.__get_cpu_energy(cpu, cpu_energy_units)
            if prev_cpu_energies[i] > cpu_energy_units:
                cpu_energy_units *= 2
            if prev_dram_energies[i] > dram_energy_units:
                dram_energy_units *= 2
            cpu_power += current_cpu_energy - prev_cpu_energies[i]
            dram_power += current_dram_energy - prev_dram_energies[i]
            prev_cpu_energies[i] = current_cpu_energy
            prev_dram_energies[i] = current_dram_energy
        return cpu_power, dram_power, prev_cpu_energies, prev_dram_energies

    def extract_power(self, interval=1):
        self.power_draws[TOTAL_CPU_TIME] = 0
        self.power_draws[TOTAL_ENERGY_CPU] = 0
        self.power_draws[TOTAL_ENERGY_MEMORY] = 0
        prev_dram_energies = []
        prev_cpu_energies = []
        for cpu in self.cpu_ids:
            power_units, cpu_energy_units, dram_energy_units, time_units = self.__get_used_units(
                cpu
            )
            prev_dram_energies.append(self.__get_dram_energy(cpu, dram_energy_units))
            prev_cpu_energies.append(self.__get_cpu_energy(cpu, cpu_energy_units))
        t0 = time.time()
        while getattr(self.thread, "do_run", True):
            time.sleep(interval)
            cpu_power, dram_power, prev_cpu_energies, prev_dram_energies = self.__get_computer_consomption(
                prev_cpu_energies, prev_dram_energies
            )
            self.power_draws[TOTAL_ENERGY_CPU] += cpu_power
            self.power_draws[TOTAL_ENERGY_MEMORY] += dram_power
            t1 = time.time()
            self.power_draws[TOTAL_CPU_TIME] += t1 - t0
            t0 = t1

    def start_measure(self):
        print("starting CPU power monitoring ...")

        if self.thread and self.thread.is_alive():
            self.stop_measure()
        self.power_draws = {}
        self.thread = threading.Thread(target=self.extract_power, args=())
        self.thread.start()

    def stop_measure(self):
        print("stoping CPU power monitoring ...")
        self.thread.do_run = False
        self.thread.join()
        self.recorded_power = self.power_draws
        self.recorded_power[TOTAL_ENERGY_ALL] = 0


if __name__ == "__main__":
    print(get_power_consumption())
