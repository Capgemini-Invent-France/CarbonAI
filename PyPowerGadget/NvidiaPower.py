import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

import re
import subprocess
import signal
import pandas as pd
import numpy as np

from PyPowerGadget.settings import *


class GpuPower:
    def __init__(self):
        self.recorded_power = {TOTAL_GPU_TIME: 0, TOTAL_ENERGY_GPU: 0}
        self.recorded_power = pd.Series(self.recorded_power)

    def start_measure(self):
        pass

    def stop_measure(self):
        pass

    def parse_power_log(self):
        pass


class NoGpuPower(GpuPower):
    def __init__(self):
        super().__init__()
        pass


class NvidiaPower(GpuPower):
    """
    Class to monitor the power usage of a gpu
    Usage :
    1. initialiase the class
    2. call start start_measure
    3. call stop stop_measure
    4. collect the results with parse_power_log
    """

    def __init__(self):
        super().__init__()
        self.log_file = (
            Path(os.path.dirname(os.path.abspath(__file__))) / NVIDIAPOWERLOG_FILENAME
        )
        self.logging_process = None

    def start_measure(self, interval=1):
        """
        Start the measure process
        Args:
            interval : interval to which log power in the log_path file
        """
        self.interval = interval
        if self.logging_process is not None:
            self.stop_measure()

        print("starting GPU power monitoring ...")

        self.logging_process = subprocess.Popen(
            [
                "nvidia-smi",
                "-f",
                self.log_file,
                "-q",
                "-d",
                "POWER",
                "-l",
                str(interval),
            ]
        )

    def stop_measure(self):
        """
        Stop the measure process if started
        """
        print("stopping GPU power monitoring ...")
        self.logging_process.send_signal(signal.SIGINT)
        self.logging_process = None

    def parse_power_log(self):
        """
        Extract power as logged in the last measure process
        Returns:
            A dataframe with all the recorded power and the ellapsed time
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
        for i, record in enumerate(records[1:]):
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
        df = pd.DataFrame(np.array([times, powers]).T, columns=["Time", "Power"])
        df["Power"] = df["Power"].astype("float32")
        df["Time"] = pd.to_datetime(df["Time"], infer_datetime_format=True)
        df["Elapsed time"] = df["Time"] - df.loc[0, "Time"]
        df["Elapsed time"] = df["Elapsed time"].dt.total_seconds()
        self.recorded_power[TOTAL_GPU_TIME] = df["Elapsed time"].iloc[-1]
        self.recorded_power[TOTAL_ENERGY_GPU] = (
            df["Power"].sum() * self.interval * 1000 / 3600
        )
