#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Python wrapper of Intel(R) Power Gadget, a software-based power estimation tool
enabled for 2nd Generation Intel(R) Core(TM) processors or later.
The software data can be logged from the command line (without running the GUI
app) using PowerLog.
"""
__all__ = [
    "PowerGadgetMac",
    "PowerGadgetWin",
    "PowerGadgetLinuxRAPL",
    "PowerGadgetLinuxMSR",
    "NoPowerGadget",
]

import abc
import datetime
import glob
import logging
import os
import re
import struct
import subprocess
import threading
import time
from pathlib import Path

import pandas as pd  # type: ignore
import psutil  # type: ignore

from .utils import (
    HOME_DIR,
    MAC_INTELPOWERLOG_FILENAME,
    PACKAGE_PATH,
    TOTAL_CPU_TIME,
    TOTAL_ENERGY_ALL,
    TOTAL_ENERGY_CPU,
    TOTAL_ENERGY_MEMORY,
    TOTAL_ENERGY_PROCESS_CPU,
    TOTAL_ENERGY_PROCESS_MEMORY,
    WIN_INTELPOWERLOG_FILENAME,
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
READ_RAPL_PATH = (
    "/sys/class/powercap/intel-rapl/intel-rapl:{}/"  # rapl_socket_id
)
RAPL_DEVICENAME_FILE = "name"
RAPL_ENERGY_FILE = "energy_uj"
RAPL_DRAM_PATH = "intel-rapl:{}:{}/"  # rapl_socket_id, rapl_device_id


class PowerGadget(abc.ABC):
    """
    Abstract wrapper to an Intel Power Gadget object instanciated \
        by a command line interface
    """

    @staticmethod
    def parse_log(powerlog_file, process_usage=None):
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
        if "Total Elapsed Time" not in content:
            LOGGER.debug(
                "The log file does not seem to be written yet, \
                we'll wait 2 secs."
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
            re.search(
                r"(?<=Total Elapsed Time \(sec\) = )(\d|\.)*", content
            ).group(0)
        )
        results[TOTAL_ENERGY_ALL] = float(
            re.search(
                r"((?<=Cumulative Package Energy_0 \(mWh\) = )|"
                r"(?<=Cumulative Processor Energy_0 \(mWh\) = ))(\d|\.)*",
                content,
            ).group(0)
        )
        results[TOTAL_ENERGY_CPU] = float(
            re.search(
                r"(?<=Cumulative IA Energy_0 \(mWh\) = )(\d|\.)*", content
            ).group(0)
        )
        results[TOTAL_ENERGY_MEMORY] = float(
            re.search(
                r"(?<=Cumulative DRAM Energy_0 \(mWh\) = )(\d|\.)*", content
            ).group(0)
        )
        if process_usage:
            # to account for the actual algorithm energy consumption we need to
            # combine the overall mesure of the machine power usage with
            # the actual algorithm CPU and memory usage
            process_usage = pd.DataFrame(
                process_usage,
                columns=["time", "process_cpu_usage", "process_memory_usage"],
            )
            powers = pd.read_csv(powerlog_file)
            powers = powers.dropna(
                subset=["Cumulative Processor Energy_0(mWh)"]
            )
            powers["System Time"] = pd.to_datetime(
                powers["System Time"], format="%H:%M:%S:%f"
            )
            powers_sec = powers.groupby(
                pd.Grouper(key="System Time", freq="S")
            )[
                [
                    "Cumulative Processor Energy_0(mWh)",
                    "Cumulative IA Energy_0(mWh)",
                    "Cumulative DRAM Energy_0(mWh)",
                ]
            ].apply(
                lambda x: x.iloc[-1] - x.iloc[0]
            )
            process_usage["time"] = process_usage["time"].dt.floor("S").dt.time
            process_usage.set_index("time", inplace=True)
            powers_sec.index = powers_sec.index.time
            power_process = pd.merge(
                powers_sec,
                process_usage,
                how="left",
                left_index=True,
                right_index=True,
            )
            # a measure is performed each second but
            # it actually takes a little more than 1s
            # so when merging on the timestamp there may be some empty values
            #  that we fill with the previous one
            power_process[
                ["process_cpu_usage", "process_memory_usage"]
            ] = power_process[
                ["process_cpu_usage", "process_memory_usage"]
            ].fillna(
                method="ffill", limit=1
            )
            results[TOTAL_ENERGY_PROCESS_CPU] = (
                power_process["Cumulative IA Energy_0(mWh)"]
                * power_process["process_cpu_usage"]
            ).sum()
            results[TOTAL_ENERGY_PROCESS_MEMORY] = (
                power_process["Cumulative DRAM Energy_0(mWh)"]
                * power_process["process_memory_usage"]
            ).sum()
        return results

    def __init__(self):
        self.record = {}
        self.thread = None

    def __get_powerlog_file(self):
        """
        Retrieve the log file where is written the PowerLog logs
        """

    def start(self):
        """
        Starts the recording processus with Intel Power Gadget
        """

    def stop_thread(self):
        self.thread.do_run = False
        self.thread.join()

    def get_computer_usage(self, process, interval=1):
        """Compute the ratio of cpu and memory used by the current process

        Parameters
        ----------
        process : psutil.Process
            the current process
        interval : int
            interval at which measure ratios

        Returns
        -------
        Tuple
            time of execution, ratio of cpu used, ration of memory used
        """
        with process.oneshot():
            process_cpu_usage = process.cpu_percent(interval=interval)
            cpu_usage = psutil.cpu_percent()
            process_cpu_usage = process_cpu_usage / (
                cpu_usage * psutil.cpu_count()
            )
            memory_global = psutil.virtual_memory()
            memory_usage = process.memory_full_info().rss / (
                memory_global.total - memory_global.available
            )
        return datetime.datetime.now(), process_cpu_usage, memory_usage

    def stop(self):
        """
        Stops the recording processus with Intel Power Gadget
        """


class NoPowerGadget(PowerGadget):
    """
    Dummy class used when no power gadget (intel power gadget, rapl, msr)
    is available. It will return empty consumption
    """

    def __init__(self):
        super().__init__()
        self.start_time = 0

    def start(self):
        self.start_time = time.time()

    def stop(self):
        end_time = time.time()
        self.record[TOTAL_ENERGY_CPU] = 0
        self.record[TOTAL_ENERGY_PROCESS_CPU] = 0
        self.record[TOTAL_ENERGY_PROCESS_MEMORY] = 0
        self.record[TOTAL_ENERGY_MEMORY] = 0
        self.record[TOTAL_CPU_TIME] = end_time - self.start_time
        self.record[TOTAL_ENERGY_ALL] = 0


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
                "We didn't find the Intel Power Gadget tool.\n"
                "Make sure it is installed (download available here : "
                "https://software.intel.com/sites/default/files/managed/91/6b/"
                "Intel%20Power%20Gadget.dmg).\n"
                "If it is installed, we looked for it here: "
                f"{powerlog_path}, try passing the path to "
                "the powerLog tool to the powerMeter."
            )
        self.powerlog_file = self.__get_powerlog_file()
        # self.thread = None
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
            check=True,
        )
        consumption = self.parse_log(self.powerlog_file)
        return consumption

    def __append_energy_usage(self, process, interval=1):
        energy_usage = self.__get_power_consumption(duration=interval)
        _, cpu_usage, memory_usage = self.get_computer_usage(
            process, interval=0
        )
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
        _, _, _ = self.get_computer_usage(
            current_process, interval=0
        )  # initialize the cpu usage
        self.__append_energy_usage(current_process, interval=interval)
        while getattr(self.thread, "do_run", True):
            self.__append_energy_usage(current_process, interval=interval)
        self.__append_energy_usage(current_process, interval=interval)

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            self.stop_thread()
        self.power_draws = []
        self.thread = threading.Thread(
            target=self.get_power_consumption, args=()
        )
        self.thread.start()

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        self.stop_thread()
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
                "We didn't find the Intel Power Gadget tool.\n"
                "Make sure it is installed (download available here :"
                "https://software.intel.com/sites/default/files/managed/91/6b/"
                "Intel%20Power%20Gadget.dmg).\n"
                "If it is installed, we looked for it here:"
                f"{self.powerlog_path}, try passing the path to the "
                "powerLog tool to the powerMeter."
            )
        self.thread = None
        self.process_usage = []

    def __get_powerlog_file(self):
        file_names = glob.glob(
            str(HOME_DIR / "Documents" / WIN_INTELPOWERLOG_FILENAME)
        )
        file_names.sort(
            key=lambda f: list(map(int, re.split(r"-|_|\.|/", f)[-7:-1]))
        )
        return Path(file_names[-1])

    def get_process_usage(self, interval=1):
        current_process = psutil.Process()
        # called once to initialize the cpu monitoring
        psutil.cpu_percent()
        while getattr(self.thread, "do_run", True):
            self.process_usage.append(
                self.get_computer_usage(current_process, interval=interval)
            )
        else:
            self.process_usage.append(
                self.get_computer_usage(current_process, interval=interval)
            )

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            LOGGER.debug(
                "another thread is alive, we are going to close it first"
            )
            self.stop_thread()
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
        _ = subprocess.run(
            '"' + str(self.powerlog_path) + '" -start', shell=True, check=True
        )

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        _ = subprocess.run(
            '"' + str(self.powerlog_path) + '" -stop', shell=True, check=True
        )
        _ = subprocess.run(
            'taskkill /IM "' + POWERLOG_TOOL_WIN + '"',
            stdout=open(os.devnull, "wb"),
            shell=True,
            check=True,
        )
        self.stop_thread()
        powerlog_file = self.__get_powerlog_file()
        self.record = self.parse_log(
            powerlog_file, process_usage=self.process_usage
        )
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
        self.power_draws = []
        self.record = {}
        self.start_time = None

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
        # ! not tested
        usages = pd.DataFrame(self.power_draws)
        usages[[TOTAL_ENERGY_CPU, TOTAL_ENERGY_MEMORY]] = (
            usages[["energy_cpu", "energy_memory"]]
            .diff()
            .fillna(usages[["energy_cpu", "energy_memory"]])
        )
        usages[TOTAL_ENERGY_PROCESS_CPU] = (
            usages[TOTAL_ENERGY_CPU] * usages["cpu_usage"]
        )
        usages[TOTAL_ENERGY_PROCESS_MEMORY] = (
            usages[TOTAL_ENERGY_MEMORY] * usages["memory_usage"]
        )
        return usages

    def __append_energy_usage(self, process, interval=1):
        # ! not tested
        energy_usage = {}
        energy_usage["energy_cpu"] = sum(
            [self.__get_cpu_energy(cpu_id) for cpu_id in self.cpu_ids]
        )
        energy_usage["energy_memory"] = sum(
            [
                self.__get_dram_energy(cpu_id, dram_id)
                for cpu_id, dram_id in self.dram_ids
            ]
        )
        _, cpu_usage, memory_usage = self.get_computer_usage(
            process, interval=interval
        )
        energy_usage["cpu_usage"] = cpu_usage
        energy_usage["memory_usage"] = memory_usage
        self.power_draws.append(energy_usage)

    def get_power_consumption(self, interval=1):
        # ! not tested
        """

        Parameters
        ----------
        interval (int)
        """
        current_process = psutil.Process()
        self.__append_energy_usage(current_process, interval=interval)
        while getattr(self.thread, "do_run", True):
            self.__append_energy_usage(current_process, interval=interval)
        self.__append_energy_usage(current_process, interval=interval)

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        self.start_time = time.time()
        self.power_draws = []
        self.record = {}
        if self.thread and self.thread.is_alive():
            self.stop_thread()
        self.thread = threading.Thread(
            target=self.get_power_consumption, args=()
        )
        self.thread.start()

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        usages = self.collect_power_usage()
        end_time = time.time()
        self.record[TOTAL_ENERGY_CPU] = (
            usages[TOTAL_ENERGY_CPU].sum() / 3600 / 1000
        )
        self.record[TOTAL_ENERGY_PROCESS_CPU] = (
            usages[TOTAL_ENERGY_PROCESS_CPU].sum() / 3600 / 1000
        )
        self.record[TOTAL_ENERGY_PROCESS_MEMORY] = (
            usages[TOTAL_ENERGY_PROCESS_MEMORY].sum() / 3600 / 1000
        )
        self.record[TOTAL_ENERGY_MEMORY] = (
            usages[TOTAL_ENERGY_MEMORY].sum() / 3600 / 1000
        )
        self.record[TOTAL_CPU_TIME] = end_time - self.start_time
        self.record[TOTAL_ENERGY_ALL] = 0


class PowerGadgetLinuxMSR(PowerGadgetLinux):
    """
    Mac OS X custom PowerGadget wrapper.
    """

    MSR_RAPL_POWER_UNIT = 0x606
    MSR_PKG_RAPL_POWER_LIMIT = 0x610
    # MSR_PKG_ENERGY_STATUS reports measured actual energy usage
    MSR_PKG_ENERGY_STATUS = 0x611
    MSR_DRAM_ENERGY_STATUS = 0x619
    MSR_PKG_PERF_STATUS = 0x613
    MSR_PKG_POWER_INFO = 0x614
    MSR_PP0_ENERGY_STATUS = 0x639

    @staticmethod
    def __read_msr(msr_file, msr_position):
        """
        Read MSR file at a specific position

        Parameters
        ----------
        msr_file : _io.TextIOWrapper
            An opened MSR file
        msr_position : int
            Position at which read the MSR file

        Returns
        -------
        int
            The value of the given MSR
        """
        os.lseek(msr_file, msr_position, os.SEEK_SET)
        return struct.unpack("Q", os.read(msr_file, 8))[0]

    def __init__(self):
        super().__init__()
        # the user needs to execute as root
        if os.getuid() != 0:
            raise PermissionError("You need to execute this program as root")
        self.thread = None
        self.power_draws = {}

    def __get_used_units(self, cpu):
        """
        Get the unit used by the MSR to encode the energy usage
        """
        msr_file = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        # Calculate the units used
        result = self.__read_msr(msr_file, self.MSR_RAPL_POWER_UNIT)
        power_units = 0.5 ** (result & 0xF)
        cpu_energy_units = 0.5 ** ((result >> 8) & 0x1F)
        dram_energy_units = cpu_energy_units
        time_units = 0.5 ** ((result >> 16) & 0xF)
        os.close(msr_file)
        return power_units, cpu_energy_units, dram_energy_units, time_units

    def __get_cpu_energy(self, cpu, unit):
        """
        Returns the CPU Energy figure
        """
        msr_file = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        result = self.__read_msr(msr_file, self.MSR_PKG_ENERGY_STATUS)
        os.close(msr_file)
        return result * unit / 3.6

    def __get_dram_energy(self, cpu, unit):
        """
        Returns the dram energy figure
        """
        msr_file = os.open(READ_MSR_PATH.format(cpu), os.O_RDONLY)
        result = self.__read_msr(msr_file, self.MSR_DRAM_ENERGY_STATUS)
        os.close(msr_file)
        return result * unit / 3.6

    def __get_computer_consumption(
        self, prev_cpu_energies, prev_dram_energies
    ):
        """
        Get the power consumption since the last measure

        Parameters
        ----------
        prev_cpu_energies : List
            List of the previous measure on the CPUs
            (One element of the list for each CPU)
        prev_dram_energies : [type]
            List of the previous measure on the DRAMs
            (One element of the list for each CPU)

        Returns
        -------
        [type]
            [description]
        """
        cpu_power = 0
        dram_power = 0
        for i, cpu in enumerate(self.cpu_ids):
            _, cpu_energy_units, dram_energy_units, _ = self.__get_used_units(
                cpu
            )
            current_dram_energy = self.__get_dram_energy(
                cpu, dram_energy_units
            )
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
        # ! not tested
        process = psutil.Process()
        self.power_draws[TOTAL_CPU_TIME] = 0
        self.power_draws[TOTAL_ENERGY_CPU] = 0
        self.power_draws[TOTAL_ENERGY_MEMORY] = 0
        prev_dram_energies = []
        prev_cpu_energies = []
        for cpu in self.cpu_ids:
            _, cpu_energy_units, dram_energy_units, _ = self.__get_used_units(
                cpu
            )
            prev_dram_energies.append(
                self.__get_dram_energy(cpu, dram_energy_units)
            )
            prev_cpu_energies.append(
                self.__get_cpu_energy(cpu, cpu_energy_units)
            )
        start_time = time.time()
        while getattr(self.thread, "do_run", True):
            # time.sleep(interval)
            _, cpu_usage, memory_usage = self.get_computer_usage(
                process, interval=interval
            )
            (
                cpu_power,
                dram_power,
                prev_cpu_energies,
                prev_dram_energies,
            ) = self.__get_computer_consumption(
                prev_cpu_energies, prev_dram_energies
            )
            self.power_draws[TOTAL_ENERGY_CPU] += cpu_power
            self.power_draws[TOTAL_ENERGY_MEMORY] += dram_power
            self.power_draws[TOTAL_ENERGY_PROCESS_CPU] += cpu_power * cpu_usage
            self.power_draws[TOTAL_ENERGY_PROCESS_MEMORY] += (
                dram_power * memory_usage
            )
            end_time = time.time()
            self.power_draws[TOTAL_CPU_TIME] += end_time - start_time
            start_time = end_time

    def start(self):
        LOGGER.info("starting CPU power monitoring ...")
        if self.thread and self.thread.is_alive():
            self.stop()
        self.power_draws = {}
        self.thread = threading.Thread(
            target=self.get_computer_consumption, args=()
        )
        self.thread.start()

    def stop(self):
        LOGGER.info("stoping CPU power monitoring ...")
        self.thread.do_run = False
        self.thread.join()
        self.record = self.power_draws
        self.record[TOTAL_ENERGY_ALL] = 0
