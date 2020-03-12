#!/usr/bin/python
# -*- coding: utf-8 -*-

__all__ = ["PowerMeter"]

import json
import datetime
import getpass
import os
import sys
import warnings
import requests

from PyPowerGadget.PowerGadget import *
from PyPowerGadget.NvidiaPower import *
from PyPowerGadget.settings import *


class PowerMeter:

    """PowerMeter is a general tool to monitor and log the power consumption of any given function.

    Parameters
    ----------
    cpu_power_log_path (optional) : str
        The path to the tool "PowerLog"
    get_country (optional) : bool
        Whether use user country location or not
    user_name (optional) : str
        The name of the user using the tool (for logging purpose)
    """

    def __init__(
        self, cpu_power_log_path="", get_country=True, user_name="", project_name=""
    ):
        self.platform = sys.platform
        if self.platform == MAC_PLATFORM:
            self.power_gadget = PowerGadgetMac(power_log_path=cpu_power_log_path)
            self.pue = 1.3  # pue for my laptop
        elif self.platform == WIN_PLATFORM:
            self.power_gadget = PowerGadgetWin(power_log_path=cpu_power_log_path)
            self.pue = 1.3  # pue for my laptop
        elif self.platform in LINUX_PLATFORMS:
            self.power_gadget = PowerGadgetLinuxMSR(power_log_path=cpu_power_log_path)
            self.pue = 1.58  # pue for a server

        self.cuda_available = self.__check_gpu()
        if self.cuda_available:
            self.gpu_power = NvidiaPower()
        else:
            self.gpu_power = NoGpuPower()

        if len(user_name) > 0:
            self.user = user_name
        else:
            self.user = getpass.getuser()
        if len(project_name) > 0:
            self.project = project_name
        else:
            self.project = self.__extract_env_name()

        self.location = "US"
        if get_country:
            self.location = self.__get_country()
        self.energy_mix_db = self.__load_energy_mix_db()
        self.energy_mix = self.__get_energy_mix()  # kgCO2e/kWh
        self.location_name = self.__get_location_name()

        self.logging_filename = PACKAGE_PATH / LOGGING_FILE
        self.logging_columns = [
            "Datetime",
            "User ID",
            COUNTRY_CODE_COLUMN,
            COUNTRY_NAME_COLUMN,
            "Platform",
            "Project name",
            TOTAL_CPU_TIME,
            TOTAL_GPU_TIME,
            TOTAL_ENERGY_ALL,
            TOTAL_ENERGY_CPU,
            TOTAL_ENERGY_GPU,
            TOTAL_ENERGY_MEMORY,
            "PUE",
            "CO2 emitted (gCO2e)",
            "Package",
            "Algorithm",
            "Algorithm's parameters",
            "Data type",
            "Data shape",
            "Comment",
        ]
        self.__init_logging_file()

    def __load_energy_mix_db(self):
        return pd.read_csv(PACKAGE_PATH / ENERGY_MIX_DATABASE, encoding="utf-8")

    def __get_energy_mix(self):
        return self.energy_mix_db.loc[
            self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location, ENERGY_MIX_COLUMN
        ].values[0]

    def __get_country(self):
        # from https://stackoverflow.com/questions/40059654/python-convert-a-bytes-array-into-json-format
        r = requests.get("http://ipinfo.io/json")
        response = r.content.decode("utf8").replace("'", '"')
        user_info = json.loads(response)
        return user_info["country"]

    def __get_location_name(self):
        return self.energy_mix_db.loc[
            self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location,
            COUNTRY_NAME_COLUMN,
        ].values[0]

    def __extract_env_name(self):
        env = "unknown"
        try:
            env = os.environ["CONDA_DEFAULT_ENV"]
        except:
            pass
        if hasattr(sys, "real_prefix"):
            env = sys.real_prefix.split("/")[-1]
        elif hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix:
            env = sys.base_prefix.split("/")[-1]
        return env

    def __check_gpu(self):
        import ctypes

        libnames = ("libcuda.so", "libcuda.dylib", "cuda.dll")
        cuda_available = False
        for libname in libnames:
            try:
                _ = ctypes.CDLL(libname)
                cuda_available = True
                break
            except OSError:
                continue
        return cuda_available

    def __aggregate_power(self, cpu_recorded_power, gpu_recorded_power):
        # print(pd.concat([cpu_recorded_power, gpu_recorded_power]))

        used_energy = self.pue * (
            cpu_recorded_power[TOTAL_ENERGY_CPU]
            + cpu_recorded_power[TOTAL_ENERGY_MEMORY]
            + gpu_recorded_power[TOTAL_ENERGY_GPU]
        )  # mWh
        co2_emitted = used_energy * self.energy_mix * 1e-3
        print(
            "This process emitted %.3fg of CO2 (using the energy mix of %s)"
            % (co2_emitted, self.location_name.encode("utf-8"))
        )

        return co2_emitted

    def mesure_power(
        self,
        func,
        package,
        algorithm,
        data_type="tabular",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        """
        Mesure the power consumption of a given function

        Parameters
        ----------
        func : python function
            The python function that will be monitored
        package : str
            A string describing the package used by this function (e.g. sklearn, Pytorch, ...)
        algorithm : str
            A string describing the algorithm used in the function monitored (e.g. RandomForestClassifier, ResNet121, ...)
        data_type : str (among : tabular, image, text, time series, other)
            A string describing the type of data used for training
        data_shape : str or tuple
            A string or tuple describing the quantity of data used
        algorithm_params (optional) : str
            A string describing the parameters used by the algorithm
        comments (optional) : str
            A string to provide any useful information

        Returns
        -------
        The result of the execution the provided function
        """
        if len(algorithm) == 0 or len(package) == 0:
            raise SyntaxError(
                "Please input a description for the function you are trying to monitor. Pass in the algorithm and the package you are trying to monitor"
            )

        def wrapper(*args, **kwargs):
            self.gpu_power.start_mesure()
            try:
                results = self.power_gadget.wrapper(func, *args, **kwargs)
            finally:
                self.gpu_power.stop_mesure()
                self.gpu_power.parse_power_log()
            self.__log_records(
                self.power_gadget.recorded_power,
                self.gpu_power.recorded_power,
                algorithm=algorithm,
                package=package,
                data_type=data_type,
                data_shape=data_shape,
                algorithm_params=algorithm_params,
                comments=comments,
            )
            return results

        return wrapper

    def __init_logging_file(self):
        if not self.logging_filename.exists():
            self.logging_filename.write_text(self.__written_columns())
        elif self.__written_columns() not in self.logging_filename.read_text(
            encoding="utf-8"
        ):
            warnings.warn(
                "The column names of the log file are not right, it will be overwritten"
            )
            time.sleep(5)
            self.logging_filename.write_text(self.__written_columns())

    def __written_columns(self):
        return ",".join(self.logging_columns)

    def __log_records(
        self,
        cpu_recorded_power,
        gpu_recorded_power,
        algorithm="",
        package="",
        data_type="tabular",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        co2_emitted = self.__aggregate_power(
            self.power_gadget.recorded_power, self.gpu_power.recorded_power
        )
        info = [
            str(datetime.datetime.now()),
            self.user,
            self.location,
            self.location_name,
            self.platform,
            self.project,
            str(cpu_recorded_power[TOTAL_CPU_TIME]),
            str(gpu_recorded_power[TOTAL_GPU_TIME]),
            str(cpu_recorded_power[TOTAL_ENERGY_ALL]),
            str(cpu_recorded_power[TOTAL_ENERGY_CPU]),
            str(gpu_recorded_power[TOTAL_ENERGY_GPU]),
            str(cpu_recorded_power[TOTAL_ENERGY_MEMORY]),
            str(self.pue),
            str(co2_emitted),
            package.replace(",", ";"),
            algorithm.replace(",", ";"),
            algorithm_params.replace(",", ";"),
            data_type.replace(",", ";"),
            str(data_shape).replace(",", ";"),
            comments.replace(",", ";"),
        ]
        self.logging_filename.open("ab").write(
            ("\n" + (",".join(info))).encode("utf-8")
        )
