#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Python wrapper of Intel(R) Power Gadget, a software-based power estimation tool
enabled for 2nd Generation Intel(R) Core(TM) processors or later.
The software data can be logged from the command line (without running the GUI
app) using PowerLog.
cf. https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html
"""
__all__ = [
    "PowerGadgetMac",
    "PowerGadgetWin",
    "PowerGadgetLinuxRAPL",
    "PowerGadgetLinuxMSR",
]

import os
from pathlib import Path
import logging
import subprocess
import re
import glob
import struct
import time
import threading
import abc
import psutil
import time

import pandas as pd

from .utils import (
    TOTAL_CPU_TIME,
    TOTAL_ENERGY_ALL,
    TOTAL_ENERGY_CPU,
    TOTAL_ENERGY_MEMORY,
    TOTAL_ENERGY_PROCESS_CPU,
    TOTAL_ENERGY_PROCESS_MEMORY,
    PACKAGE_PATH,
    MAC_INTELPOWERLOG_FILENAME,
    HOME_DIR,
    WIN_INTELPOWERLOG_FILENAME,
    POWERLOG_PATH_LINUX,
)

LOGGER = logging.getLogger(__name__)

DMG_PATH = Path("/tmp/IntelPowerGadget.dmg")
MSI_PATH = Path("C:\\tmp\\IntelPowerGadget.msi")

POWERLOG_PATH_MAC = Path("/Applications/Intel Power Gadget/PowerLog")
POWERLOG_PATH_WIN = [
    Path("/Program Files/Intel/Power Gadget 3.6"),
    Path("/Program Files/Intel/Power Gadget 3.5"),
]
POWERLOG_TOOL_WIN = "IntelPowerGadget.exe"


CPU_IDS_DIR = "/sys/devices/system/cpu/cpu*/topology/physical_package_id"
READ_MSR_PATH = "/dev/cpu/{}/msr"
READ_RAPL_PATH = "/sys/class/powercap/intel-rapl/intel-rapl:{}/"  # rapl_socket_id
RAPL_DEVICENAME_FILE = "name"
RAPL_ENERGY_FILE = "energy_uj"
RAPL_DRAM_PATH = "intel-rapl:{}:{}/"  # rapl_socket_id, rapl_device_id


class PowerGadget(abc.ABC):
    """
    Abstract wrapper to an Intel Power Gadget object instanciated by a command line interface
    """

    @staticmethod
    def parse_log(powerlog_file):
        """
        From the file made by PowerLog, we extract relevant information.

        Parameters
        ----------
        powerlog_file
            Pathlib.Path instance
        Returns
        -------
        results (dict)
            relevant information such as "Cumulative Package Energy (mWh)",
            "Cumulative IA Energy (mWh)" or "Cumulative GPU Energy (mWh)"
        """
        content = powerlog_file.read_text()
        if not "Total Elapsed Time" in content:
            LOGGER.debug(
                "The log file does not seem to written yet, we'll wait 2 secs."
            )
            time.sleep(2)
            content = powerlog_file.read_text()
        results = {
            TOTAL_CPU_TIME: 0,
            TOTAL_ENERGY_ALL: 0,
            TOTAL_ENERGY_CPU: 0,
            TOTAL_ENERGY_MEMORY: 0,
        }
        results[TOTAL_CPU_TIME] = float(
            re.search(r"(?<=Total Elapsed Time \(sec\) = )(\d|\.)*", content).group(0)
        )
        results[TOTAL_ENERGY_ALL] = float(
            re.search(
                r"((?<=Cumulative Package Energy_0 \(mWh\) = )|(?<=Cumulative Processor Energy_0 \(mWh\) = ))(\d|\.)*",
                content,
            ).group(0)
        )
        results[TOTAL_ENERGY_CPU] = float(
            re.search(r"(?<=Cumulative IA Energy_0 \(mWh\) = )(\d|\.)*", content).group(
                0
            )
        )
        results[TOTAL_ENERGY_MEMORY] = float(
            re.search(
                r"(?<=Cumulative DRAM Energy_0 \(mWh\) = )(\d|\.)*", content
            ).group(0)
        )

        return results

    def __init__(self):
        self.record = {}

    def __get_powerlog_file(self):
        """
        Retrieve the log file where is written the PowerLog logs
        """
        pass

    def start(self):
        """
        Starts the recording processus with Intel Power Gadget
        """
        pass

    def stop(self):
        """
        Stops the recording processus with Intel Power Gadget
        """
        pass


class PowerGadgetMac(PowerGadget):
    """
    Mac OS X custom PowerGadget wrapper.
    """

    def __init__(self, powerlog_path=""):
        super().__init__()
        if powerlog_path:
            self.powerlog_path = Path(powerlog_path)
        else:
            self.powerlog_path = POWERLOG_PATH_MAC

        if not self.powerlog_path.exists():
            raise ModuleNotFoundError(
                "We didn't find the Intel Power Gadget tool. \nMake sure it is installed (download available here : https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg).\nIf it is installed, we looked for it here:"
                + str(self.powerlog_path)
                + ", try passing the path to the powerLog tool to the powerMeter."
            )
        self.powerlog_file = self.__get_powerlog_file()
        self.thread = None
        self.power_draws = []

    def __get_powerlog_file(self):
        return PACKAGE_PATH / MAC_INTELPOWERLOG_FILENAME

    def __get_power_consumption(self, duration=1, resolution=500):
        """
        Retrieve all the available power consumptions with PowerLog using the
        following cli: PowerLog [-resolution ] -duration  [-verbose] [-file ]

        Parameters:
        -----------
        duration, resolution (int):
            cli's arguments

        Returns:
        --------
        consumption (dict)
        """
        _ = subprocess.run(
            [
                self.powerlog_path,
                "-resolution",
                str(resolution),
                "-duration",
                str(duration),
                "-file",
                self.powerlog_file,
            ],
            stdout=open(os.devnull, "wb"),
        )
        consumption = self.parse_log(self.powerlog_file)
        return consumption

    def __get_computer_usage(self, process):
        """
        Records the cpu percent usage and memory usage since last call (will return 0 when first call is performed)
        Note: The cpu usage is not split evenly between all available CPUs and must be divided by the number of cpu

        Parameters
        ----------
        process : psutil.Process
            The current running process as given by psutil

        Returns
        -------
        Tuple
            The recorded CPU percent usage and the memory usage
        """
        process_usage = process.as_dict()
        cpu_usage = process_usage["cpu_percent"] / 100
        memory_usage = process_usage["memory_percent"] / 100
        return cpu_usage, memory_usage

    def __append_energy_usage(self, process, interval=1):
        energy_usage = self.__get_power_consumption(duration=interval)
        cpu_usage, memory_usage = self.__get_computer_usage(process)
        energy_usage[TOTAL_ENERGY_PROCESS_CPU] = (
            energy_usage[TOTAL_ENERGY_CPU] * cpu_usage
        )
        energy_usage[TOTAL_ENERGY_PROCESS_MEMORY] = (
            energy_usage[TOTAL_ENERGY_MEMORY] * memory_usage
        )
        self.power_draws.append(energy_usage)

    def get_power_consumption(self, interval=1):
        """

        Parameters
        ----------
        interval (int)
        """
        current_process = psutil.Process()
        _, _ = self.__get_computer_usage(current_process)  # initialize the cpu usage
        self.__append_energy_usage(current_process, interval=interval)
        while getattr(self.thread, "do_run", True):
            self.__append_energy_usage(current_process, interval=interval)
        self.__append_energy_usage(current_process, interval=interval)

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            self.stop()
        self.power_draws = []
        self.thread = threading.Thread(target=self.get_power_consumption, args=())
        self.thread.start()

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        self.thread.do_run = False
        self.thread.join()
        self.record = pd.DataFrame.from_records(self.power_draws)
        self.record = self.record.sum(axis=0)


class PowerGadgetWin(PowerGadget):
    """
    Windows custom PowerGadget wrapper.
    """

    def __init__(self, powerlog_path=""):
        super().__init__()
        if powerlog_path:
            self.powerlog_path = Path(powerlog_path)
        else:
            # Try different version of the powerlog path on windows
            for path_win in POWERLOG_PATH_WIN:
                if path_win.exists():
                    self.powerlog_path = path_win / POWERLOG_TOOL_WIN
                    break
        if not self.powerlog_path.exists():
            raise ModuleNotFoundError(
                "We didn't find the Intel Power Gadget tool. \nMake sure it is installed (download available here : https://software.intel.com/file/823776/download).\nIf it is installed, we looked for it here:"
                + str(self.powerlog_path)
                + ", try passing the path to the powerLog tool to the powerMeter."
            )

    def __get_powerlog_file(self):
        file_names = glob.glob(str(HOME_DIR / "Documents" / WIN_INTELPOWERLOG_FILENAME))
        file_names.sort(key=lambda f: list(map(int, re.split(r"-|_|\.|/", f)[-7:-1])))
        return Path(file_names[-1])

    def __stop_thread(self):
        self.thread.do_run = False
        self.thread.join()

    def __get_computer_usage(self, process, interval):
        with process.oneshot():
            cpu_usage = process.cpu_percent(interval=interval) / 100
            memory_usage = process.memory_percent() / 100
        return cpu_usage, memory_usage

    def get_process_usage(self, interval=1):
        current_process = psutil.Process()
        while getattr(self.thread, "do_run", True):
            self.process_usage.append(
                self.__get_computer_usage(current_process, interval=interval)
            )
        else:
            self.process_usage.append(
                self.__get_computer_usage(current_process, interval=interval)
            )

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            LOGGER.debug("another thread is alive, we are going to close it first")
            self.__stop_thread()
        _ = subprocess.Popen(
            '"' + str(self.powerlog_path) + '" /min',
            stdin=None,
            stdout=None,
            stderr=None,
            shell=True,
        )
        time.sleep(1)
        self.thread = threading.Thread(target=self.get_process_usage, args=())
        self.thread.start()
        _ = subprocess.run('"' + str(self.powerlog_path) + '" -start', shell=True)

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        _ = subprocess.run('"' + str(self.powerlog_path) + '" -stop', shell=True)
        _ = subprocess.run(
            'taskkill /IM "' + POWERLOG_TOOL_WIN + '"',
            stdout=open(os.devnull, "wb"),
            shell=True,
        )
        self.__stop_thread()
        powerlog_file = self.__get_powerlog_file()
        self.record = self.parse_log(powerlog_file)
        os.remove(powerlog_file)


class PowerGadgetLinux(PowerGadget):
    """
    Linux custom PowerGadget wrapper.
    """

    @staticmethod
    def __get_cpu_ids():
        """
        Returns the cpu id of this machine
        """
        cpu_ids = []
        for filename in glob.glob(CPU_IDS_DIR):
            with open(filename, "r") as f:
                package_id = int(f.read())
            if package_id not in cpu_ids:
                cpu_ids.append(package_id)
        return cpu_ids

    def __init__(self):
        super().__init__()
        self.cpu_ids = self.__get_cpu_ids()


class PowerGadgetLinuxRAPL(PowerGadgetLinux):
    """
    RAPL Linux custom PowerGadget wrapper.
    """

    @staticmethod
    def __get_cpu_energy(cpu):
        """
        Returns the CPU Energy figure
        """
        cpu_energy_file = Path(READ_RAPL_PATH.format(cpu)) / RAPL_ENERGY_FILE
        energy = int(cpu_energy_file.read_text())
        return energy

    @staticmethod
    def __get_dram_energy(cpu, dram):
        """
        Returns the dram energy figure
        """
        dram_energy_file = (
            Path(READ_RAPL_PATH.format(cpu))
            / (RAPL_DRAM_PATH.format(cpu, dram))
            / RAPL_ENERGY_FILE
        )
        energy = int(dram_energy_file.read_text())
        return energy

    def __init__(self):
        super().__init__()
        self.dram_ids = self.__get_drams_ids()

    def __get_drams_ids(self):
        """
        Returns the drams id of this machine
        """
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

    def start(self):
        print("starting CPU power monitoring ...")
        self.start_time = time.time()
        # self.power_draws = []
        self.record = {}
        self.cpu_powers = []
        self.dram_powers = []
        for cpu_id in self.cpu_ids:
            self.cpu_powers.append(self.__get_cpu_energy(cpu_id))
        for cpu_id, dram_id in self.dram_ids:
            self.dram_powers.append(self.__get_dram_energy(cpu_id, dram_id))

    def stop(self):
        print("stoping CPU power monitoring ...")
        self.collect_power_usage()
        self.record[TOTAL_ENERGY_CPU] = sum(self.cpu_powers) / 3600 / 1000
        self.record[TOTAL_ENERGY_MEMORY] = sum(self.dram_powers) / 3600 / 1000
        end_time = time.time()
        self.record[TOTAL_CPU_TIME] = end_time - self.start_time
        self.record[TOTAL_ENERGY_ALL] = 0


class PowerGadgetLinuxMSR(PowerGadgetLinux):
    """
    Mac OS X custom PowerGadget wrapper.
    """

    MSR_RAPL_POWER_UNIT = 0x606
    MSR_PKG_RAPL_POWER_LIMIT = 0x610
    MSR_PKG_ENERGY_STATUS = 0x611  #  reports measured actual energy usage
    MSR_DRAM_ENERGY_STATUS = 0x619
    MSR_PKG_PERF_STATUS = 0x613
    MSR_PKG_POWER_INFO = 0x614
    MSR_PP0_ENERGY_STATUS = 0x639

    @staticmethod
    def __read_msr(fd, msr):
        """
        TODO: add docstring
        """
        os.lseek(fd, msr, os.SEEK_SET)
        return struct.unpack("Q", os.read(fd, 8))[0]

    def __init__(self):
        super().__init__()
        # the user needs to execute as root
        if os.geteuid() != 0:
            raise PermissionError("You need to execute this program as root")
        self.thread = None
        self.power_draws = {}

    def __get_used_units(self, cpu):
        """
        TODO: add docstring
        """
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
        """
        Returns the CPU Energy figure
        """
        fd = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        result = self.__read_msr(fd, self.MSR_PKG_ENERGY_STATUS)
        os.close(fd)
        return result * unit / 3.6

    def __get_dram_energy(self, cpu, unit):
        """
        Returns the dram energy figure
        """
        fd = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        result = self.__read_msr(fd, self.MSR_DRAM_ENERGY_STATUS)
        os.close(fd)
        return result * unit / 3.6

    def __get_computer_consumption(self, prev_cpu_energies, prev_dram_energies):
        """
        TODO: add docs
        Retrieve all the available power consumptions with PowerLog using the
        following cli: PowerLog [-resolution ] -duration  [-verbose] [-file ]

        Parameters:
        -----------
        prev_cpu_energies, prev_dram_energies (list):

        Returns:
        --------
        cpu_power, dram_power (int)
        prev_cpu_energies, prev_dram_energies (list)
        """
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

    def get_computer_consumption(self, interval=1):
        """

        Parameters
        ----------
        interval (int)
        """
        self.power_draws[TOTAL_CPU_TIME] = 0
        self.power_draws[TOTAL_ENERGY_CPU] = 0
        self.power_draws[TOTAL_ENERGY_MEMORY] = 0
        prev_dram_energies = []
        prev_cpu_energies = []
        for cpu in self.cpu_ids:
            _, cpu_energy_units, dram_energy_units, _ = self.__get_used_units(cpu)
            prev_dram_energies.append(self.__get_dram_energy(cpu, dram_energy_units))
            prev_cpu_energies.append(self.__get_cpu_energy(cpu, cpu_energy_units))
        t0 = time.time()
        while getattr(self.thread, "do_run", True):
            time.sleep(interval)
            (
                cpu_power,
                dram_power,
                prev_cpu_energies,
                prev_dram_energies,
            ) = self.__get_computer_consumption(prev_cpu_energies, prev_dram_energies)
            self.power_draws[TOTAL_ENERGY_CPU] += cpu_power
            self.power_draws[TOTAL_ENERGY_MEMORY] += dram_power
            t1 = time.time()
            self.power_draws[TOTAL_CPU_TIME] += t1 - t0
            t0 = t1

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            self.stop()
        self.power_draws = {}
        self.thread = threading.Thread(target=self.get_computer_consumption, args=())
        self.thread.start()

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        self.thread.do_run = False
        self.thread.join()
        self.record = self.power_draws
        self.record[TOTAL_ENERGY_ALL] = 0
