#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Main Python class or entrypoint to monitor the power consumption of an algorithm. 
"""

__all__ = ["PowerMeter"]

from pathlib import Path
import logging
import traceback
import json
import datetime
import getpass
import os
import sys
import requests
import pandas as pd

from .PowerGadget import *
from .NvidiaPower import *
from .utils import *


LOGGER = logging.getLogger(__name__)


class PowerMeter:
    """PowerMeter is a general tool to monitor and log the power consumption of any given function.

    Parameters
    ----------
    - project_name (optional) : str
        Name of the project you are working on (default is folder_name)
    - cpu_power_log_path (optional) : str
        The path to the tool "PowerLog"
    - get_country (optional) : bool
        Whether use user country location or not
    - user_name (optional) : str
        The name of the user using the tool (for logging purpose)
    - filepath (optional) : str
        Path of the file where all the green ai logs are written
    - api_endpoint (optional):
        Endpoint of the API
    """

    LAPTOP_PUE = 1.3  # pue for my laptop
    SERVER_PUE = 1.58  # pue for a server
    DEFAULT_LOCATION = "FR"

    @staticmethod
    def __load_energy_mix_db():
        return pd.read_csv(PACKAGE_PATH / ENERGY_MIX_DATABASE, encoding="utf-8")

    @staticmethod
    def __extract_env_name():
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

    @staticmethod
    def __check_gpu():
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
 
    @staticmethod
    def __get_country():
        """
        Retrieve the ISO code country
        Beware of the encoding
        cf. from https://stackoverflow.com/questions/40059654/python-convert-a-bytes-array-into-json-format
        """
        request = requests.get("http://ipinfo.io/json")
        response = request.content.decode("utf8").replace("'", '"')
        user_info = json.loads(response)
        return user_info["country"]

    @classmethod
    def from_config(cls, path):
        """ """
        with open(path) as file:
            args = json.load(file)
        return cls(**args)

    def __init__(
        self, project_name="", program_name="", client_name="", cpu_power_log_path="",
        get_country=True, user_name="", filepath=None,
        api_endpoint=None, location="", is_online=True,
        output_format='csv'
    ):
        self.platform = sys.platform
        if self.platform == "darwin":
            self.power_gadget = PowerGadgetMac(
                powerlog_path=cpu_power_log_path)
            self.pue = self.LAPTOP_PUE  # pue for my laptop
        elif self.platform == "win32":
            self.power_gadget = PowerGadgetWin(
                powerlog_path=cpu_power_log_path)
            self.pue = self.LAPTOP_PUE  # pue for my laptop
        elif self.platform in ["linux", "linux2"]:
            if POWERLOG_PATH_LINUX.exists():
                self.power_gadget = PowerGadgetLinuxRAPL()
            else:
                self.power_gadget = PowerGadgetLinuxMSR()
            self.pue = self.SERVER_PUE  # pue for a server

        self.cuda_available = self.__check_gpu()
        if self.cuda_available:
            self.gpu_power = NvidiaPower()
        else:
            self.gpu_power = NoGpuPower()

        if user_name:
            self.user = user_name
        else:
            self.user = getpass.getuser()

        if project_name:
            self.project = project_name
        else:
            self.project = self.__extract_env_name()

        if program_name:
            self.program_name = program_name
        else:
            self.program_name = "--"

        if client_name:
            self.client_name = client_name
        else:
            self.client_name = "--"

        if is_online:
            self.location = self.__get_country()
        elif location:
            self.location = location
        else:
            self.location = self.DEFAULT_LOCATION

        self.is_online = is_online
        self.energy_mix_db = self.__load_energy_mix_db()
        self.energy_mix = self.__get_energy_mix()  # kgCO2e/kWh
        self.location_name = self.__get_location_name()

        if not filepath:
            LOGGER.info("No current filepath")
            self.filepath = Path.cwd() / "emissions.csv"
        else:
            LOGGER.info("filepath ok then")
            self.filepath = filepath
        
        self.output_format = output_format

        if api_endpoint:
            LOGGER.info("api endpoint given")
            self.api_endpoint = api_endpoint
        else:
            LOGGER.info("No current api endpoint")
            self.api_endpoint = ""

        self.logging_filename = PACKAGE_PATH / LOGGING_FILE

    def __get_energy_mix(self):
        if not (self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location).any():
            raise NameError(
                "The location inputed was not found, make sure you wrote the isocode of your country. You used "+self.location)
        return self.energy_mix_db.loc[
            self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location, ENERGY_MIX_COLUMN
        ].values[0]

    def __get_location_name(self):
        return self.energy_mix_db.loc[
            self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location,
            COUNTRY_NAME_COLUMN,
        ].values[0]


    def __aggregate_power(self, cpu_record, gpu_record):
        """
        Implement the cO2 emission value

        Parameters:
        -----------
        cpu_record, gpu_record (dict):
            Respectively CPU and GPU's records
        
        Returns
        -------
        co2_emitted (float)
        """
        used_energy = self.pue * (
            cpu_record[TOTAL_ENERGY_CPU]
            + cpu_record[TOTAL_ENERGY_MEMORY]
            + gpu_record[TOTAL_ENERGY_GPU]
        )  # mWh
        co2_emitted = used_energy * self.energy_mix * 1e-3
        LOGGER.info(
            "This process emitted %.3fg of CO2 (using the energy mix of %s)"
            % (co2_emitted, self.location_name)
        )

        return co2_emitted

    def measure_power(
        self,
        package,
        algorithm,
        data_type="",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        """
        A decorator to measure the power consumption of a given function

        Parameters
        ----------
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
        """
        if not algorithm or not package:
            raise SyntaxError(
                "Please input a description for the function you are trying to monitor. Pass in the algorithm and the package you are trying to monitor"
            )

        def decorator(func):
            def wrapper(*args, **kwargs):
                self.start_measure(
                    package,
                    algorithm,
                    data_type=data_type,
                    data_shape=data_shape,
                    algorithm_params=algorithm_params,
                    comments=comments,
                )
                try:
                    results = func(*args, **kwargs)
                finally:
                    self.stop_measure()
                return results

            return wrapper

        return decorator

    def __set_used_arguments(
        self,
        package,
        algorithm,
        data_type="",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        self.used_package = str(package) if package else ""
        self.used_algorithm = str(algorithm) if algorithm else ""
        self.used_data_type = str(data_type) if data_type else ""
        self.used_data_shape = str(data_shape) if data_shape else ""
        self.used_algorithm_params = str(
            algorithm_params) if algorithm_params else ""
        self.used_comments = str(comments) if comments else ""

    def __call__(
        self,
        package,
        algorithm,
        data_type="",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        """
        The function used by the with statement

        Parameters
        ----------
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

        """
        self.__set_used_arguments(
            package,
            algorithm,
            data_type=data_type,
            data_shape=data_shape,
            algorithm_params=algorithm_params,
            comments=comments,
        )
        return self

    def __enter__(self,):
        self.start_measure(
            self.used_package,
            self.used_algorithm,
            data_type=self.used_data_type,
            data_shape=self.used_data_shape,
            algorithm_params=self.used_algorithm_params,
            comments=self.used_comments,
        )

    def __exit__(self, type, value, traceback):
        self.stop_measure()

    def start_measure(
        self,
        package,
        algorithm,
        data_type="",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        """
        Starts mesuring the power consumption of a given sample of code

        Parameters
        ----------
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

        """
        self.gpu_power.start()
        self.power_gadget.start()
        self.__set_used_arguments(
            package,
            algorithm,
            data_type=data_type,
            data_shape=data_shape,
            algorithm_params=algorithm_params,
            comments=comments,
        )

    def stop_measure(self):
        """
        Stops the measure started with start_measure

        """
        self.power_gadget.stop()
        self.gpu_power.stop()
        self.gpu_power.parse_log()
        self.__log_records(
            self.power_gadget.record,  # must be a dict
            self.gpu_power.record,  # must be a dict
            algorithm=self.used_algorithm,
            package=self.used_package,
            data_type=self.used_data_type,
            data_shape=self.used_data_shape,
            algorithm_params=self.used_algorithm_params,
            comments=self.used_comments,
        )

    # def __init_logging_file(self):
    #     if not self.logging_filename.exists():
    #         self.logging_filename.write_text(self.__written_columns())
    #     elif self.__written_columns() not in self.logging_filename.read_text(
    #         encoding="utf-8"
    #     ):
    #         warnings.warn(
    #             "The column names of the log file are not right, it will be overwritten"
    #         )
    #         time.sleep(5)
    #         self.logging_filename.write_text(self.__written_columns())

    # def __written_columns(self):
    #     return ",".join(self.logging_columns)

    def __record_data_to_server(self, info):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(info)
        try:
            response = requests.request(
                "POST", self.api_endpoint, headers=headers, data=data, timeout=1
            )
            print("reponse   ")
            print(response.text)
            return response.status_code
        except requests.exceptions.Timeout:
            return 408

    def __record_data_to_csv_file(self, info):
        try:
            data = pd.DataFrame(info, index=[0])
            if Path(self.filepath).exists():
                data.to_csv(self.filepath, mode="a",
                            index=False, header=False)
            else:
                data.to_csv(self.filepath, index=False)
            return True
        except:
            LOGGER.error("* error during the csv writing process *")
            return False

    def __record_data_to_excel_file(self, info):
        try:
            
            if Path(self.filepath).exists():
                data = pd.read_excel(self.filepath).append(info, ignore_index=True)
                data.to_excel(self.filepath,
                            index=False)
            else:
                data = pd.DataFrame(info, index=[0])
                data.to_excel(self.filepath, index=False)
            return True
        except:
            LOGGER.error("* error during the writing process in an excel file *")
            LOGGER.error(traceback.format_exc())
            return False

    def __record_data_to_file(self, info):
        """
        Only two options so far: CSV or EXCEL
        """
        if self.filepath.endswith('.csv'):
            return self.__record_data_to_csv_file(info)
        elif self.filepath.endswith('.xls') or self.filepath.endswith('.xlsx'):
            return self.__record_data_to_excel_file(info)
        else:
            LOGGER.info('unknown format: it should be either .csv, .xls or .xlsx')
            return self.__record_data_to_excel_file(info)

    def __log_records(
        self,
        cpu_recorded_power,
        gpu_recorded_power,
        algorithm="",
        package="",
        data_type="",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        co2_emitted = self.__aggregate_power(
            self.power_gadget.record, self.gpu_power.record
        )
        payload = {
            "Datetime": str(datetime.datetime.now()),
            "Country": self.location_name,
            "Platform": self.platform,
            "User ID": self.user,
            "ISO": self.location,
            "Project name": self.project,
            "Program name": self.program_name,
            "Client name": self.client_name,
            "Total Elapsed CPU Time (sec)": cpu_recorded_power[TOTAL_CPU_TIME],
            "Total Elapsed GPU Time (sec)": gpu_recorded_power[TOTAL_GPU_TIME],
            "Cumulative Package Energy (mWh)":cpu_recorded_power[TOTAL_ENERGY_ALL],
            "Cumulative IA Energy (mWh)": cpu_recorded_power[TOTAL_ENERGY_CPU],
            "Cumulative GPU Energy (mWh)": gpu_recorded_power[TOTAL_ENERGY_GPU],
            "Cumulative DRAM Energy (mWh)": cpu_recorded_power[TOTAL_ENERGY_MEMORY],
            "PUE": self.pue,
            "CO2 emitted (gCO2e)": co2_emitted,
            "Package": package,
            "Algorithm": algorithm,
            "Algorithm's parameters": algorithm_params,
            "Data type": data_type,
            "Data shape": data_shape,
            "Comment": comments,
        }
        written = self.__record_data_to_file(payload)
        LOGGER.info("* recorded into a file? {}*".format(written))

        if self.is_online:
            response_status_code = self.__record_data_to_server(payload)
            if response_status_code >= 400:
                LOGGER.warn(
                    "We couldn't upload the recorded data to the server, we are going to record it for a later upload"
                )
                # can't upload we'll record the data
                data = pd.DataFrame(payload, index=[0])
                if self.logging_filename.exists():
                    data.to_csv(self.logging_filename, mode="a",
                                index=False, header=False)
                else:
                    data.to_csv(self.logging_filename, index=False)

            if response_status_code == 200:
                # we successfully uploaded, check if there are other locally recorded data
                if self.logging_filename.exists():
                    data = pd.read_csv(self.logging_filename, index_col=None)
                    payloads = data.to_dict(orient="records")
                    for i, payload in enumerate(payloads):
                        res_status_code = self.__record_data_to_server(payload)
                        if res_status_code != 200:
                            data.iloc[i:].to_csv(
                                self.logging_filename, index=False)
                            break
                    else:
                        self.logging_filename.unlink()
