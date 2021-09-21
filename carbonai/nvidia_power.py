#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Python classes monitoring GPU's power usage
during a time delimited between a start and a stop methods
"""
__all__ = ["NoGpuPower", "NvidiaPower"]

import abc
import logging
import os
import re
import signal
import subprocess
from pathlib import Path

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from .utils import TOTAL_ENERGY_GPU, TOTAL_GPU_TIME

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

    def stop(self):
        """
        Stops the recording processus
        """

    def parse_log(self):
        """
        Extract relevant information from the logs.
        """


class NoGpuPower(GpuPower):
    """
    Class used when no GPU is available
    """

    def __init__(self):
        super().__init__()


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
            Path(os.path.dirname(os.path.abspath(__file__)))
            / NVIDIAPOWERLOG_FILENAME
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
                "Logging file not found, make sure you started to \
                    run a measure"
            )
        content = self.log_file.read_text()
        regex_power = r"Power Draw +: (.*) W"
        regex_time = r"Timestamp +: (.*)"
        times = re.findall(regex_time, content)
        powers = re.findall(regex_power, content)
        if len(times) != len(powers):
            min_len = min(len(times), len(powers))
            times = times[:min_len]
            powers = powers[:min_len]
        results = pd.DataFrame(
            np.array([times, powers]).T, columns=["Time", "Power"]
        )
        results["Power"] = results["Power"].astype("float32")
        results["Time"] = pd.to_datetime(
            results["Time"], infer_datetime_format=True
        )
        results["Elapsed time"] = results["Time"] - results.loc[0, "Time"]
        results["Elapsed time"] = results["Elapsed time"].dt.total_seconds()
        self.record[TOTAL_GPU_TIME] = results["Elapsed time"].iloc[-1]
        self.record[TOTAL_ENERGY_GPU] = (
            results["Power"].sum() * self.interval * 1000 / 3600
        )
