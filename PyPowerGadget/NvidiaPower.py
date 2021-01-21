#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Python classes monitoring GPU's power usage
during a time delimited between a start and a stop methods
"""
__all__ = ['NoGpuPower', 'NvidiaPower']

import abc
import os
from pathlib import Path
import logging
import re
import subprocess
import signal
import pandas as pd
import numpy as np

from PyPowerGadget.utils import TOTAL_GPU_TIME, TOTAL_ENERGY_GPU


LOGGER = logging.getLogger(__name__)

NVIDIAPOWERLOG_FILENAME = "nvidiaPowerLog.csv"

class GpuPower(abc.ABC):
    """
    Class to monitor the power usage of a gpu
    Usage :
    1. initialiase the class
    2. call start
    3. call stop
    4. collect the results with parse_log
    """
    def __init__(self):
        self.record = {TOTAL_GPU_TIME: 0, TOTAL_ENERGY_GPU: 0}

    def start(self):
        """
        Starts the recording processus
        """
        pass

    def stop(self):
        """
        Stops the recording processus
        """
        pass

    def parse_log(self):
        """
        Extract relevant information from the logs.
        """
        pass


class NoGpuPower(GpuPower):
    """
    TODO: add docstring. A quoi sert cette classe ?
    """
    def __init__(self):
        super().__init__()
        pass


class NvidiaPower(GpuPower):
    """
    NVIDIA-based GPU class

    Parameters
    ----------
    interval (int)
        interval to which log power in the log_path file
    """

    def __init__(self, interval=1):
        super().__init__()
        self.log_file = (
            Path(os.path.dirname(os.path.abspath(__file__))) / NVIDIAPOWERLOG_FILENAME
        )
        self.logging_process = None
        self.interval = interval

    def start(self):
        """
        Start the measure process
        """
        if self.logging_process is not None:
            self.stop()

        LOGGER.info("starting GPU power monitoring ...")

        self.logging_process = subprocess.Popen(
            [
                "nvidia-smi",
                "-f",
                str(self.log_file),
                "-q",
                "-d",
                "POWER",
                "-l",
                str(self.interval),
            ]
        )

    def stop(self):
        """
        Stop the measure process if started
        """
        LOGGER.info("stopping GPU power monitoring ...")
        self.logging_process.send_signal(signal.SIGINT)
        self.logging_process = None

    def parse_log(self):
        """
        Extract power as logged in the last measure process
        Returns:
        -------
        results (pandas.DataFrame)
            all records with associated ellapsed times
        """
        if not self.log_file.exists():
            raise FileNotFoundError(
                "Logging file not found, make sure you started to run a measure"
            )
        content = self.log_file.read_text()
        regex_power = "(?<=Power Draw                  : )(.*)(?= W)"
        regex_time = "(?<=Timestamp                           : )(.*)"
        records = content.split("==============NVSMI LOG==============")
        prev_power = 0
        times = []
        powers = []
        for record in records[1:]:
            regex_power = "(?<=Power Draw                  : )(.*)(?= W)"
            regex_time = "(?<=Timestamp                           : )(.*)"
            time = re.search(regex_time, record).group(0)
            power = re.search(regex_power, record)
            if power:
                power = power.group(0)
            else:
                power = prev_power
            prev_power = power
            times.append(time)
            powers.append(power)
        results = pd.DataFrame(np.array([times, powers]).T, columns=["Time", "Power"])
        results["Power"] = results["Power"].astype("float32")
        results["Time"] = pd.to_datetime(results["Time"], infer_datetime_format=True)
        results["Elapsed time"] = results["Time"] - results.loc[0, "Time"]
        results["Elapsed time"] = results["Elapsed time"].dt.total_seconds()
        self.record[TOTAL_GPU_TIME] = results["Elapsed time"].iloc[-1]
        self.record[TOTAL_ENERGY_GPU] = (
            results["Power"].sum() * self.interval * 1000 / 3600
        )
