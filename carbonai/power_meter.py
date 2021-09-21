#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
PowerMeter
---------
Main Python class or entrypoint to monitor the power consumption of
an algorithm.
"""

__all__ = ["PowerMeter"]

import datetime
import getpass
import json
import logging
import os
import shutil
import sys
import traceback
import warnings
from pathlib import Path

import pandas as pd  # type: ignore
import requests

from .nvidia_power import NoGpuPower, NvidiaPower
from .power_gadget import (
    NoPowerGadget,
    PowerGadgetLinuxMSR,
    PowerGadgetLinuxRAPL,
    PowerGadgetMac,
    PowerGadgetWin,
)
from .utils import (
    AVAILABLE_STEPS,
    COUNTRY_CODE_COLUMN,
    COUNTRY_NAME_COLUMN,
    ENERGY_MIX_COLUMN,
    ENERGY_MIX_DATABASE,
    LOGGING_FILE,
    MSR_PATH_LINUX_TEST,
    PACKAGE_PATH,
    POWERLOG_PATH_LINUX,
    TOTAL_CPU_TIME,
    TOTAL_ENERGY_ALL,
    TOTAL_ENERGY_CPU,
    TOTAL_ENERGY_GPU,
    TOTAL_ENERGY_MEMORY,
    TOTAL_ENERGY_PROCESS_CPU,
    TOTAL_ENERGY_PROCESS_MEMORY,
    TOTAL_GPU_TIME,
    match,
    normalize,
)

LOGGER = logging.getLogger(__name__)


class PowerMeter:
    """
    PowerMeter is a general tool to monitor and log the power consumption of
    any given function.

    Depending on the platform and hardware used, it allows to measure the
    power usage of the CPU,the DRAM and the GPU. The measure is, then,
    converted to CO2 emissions depending on the country set and the PUE
    of the machine (background on the PUE `here`_). You can chose to log the
    results locally or send it to an endpoint.

    Parameters
    ----------
    project_name : str, default current_directory_name
        Name of the project you are working on.
    program_name : str, optional
        Name of the program you are working on.
    client_name : str, optional
        Name of the client you are working for.
    user_name : str, default computer_user_name
        The name of the user using the tool (for logging purpose).
    cpu_power_log_path : str, optional
        The path to the tool "PowerLog" or "powercap" or "IntelPowerGadget".
    get_country : bool, default True
        Whether to retrieve user country location or not (uses the user IP).
    location : str, optional
        Country ISO Code available `here
        <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements>`_

        Must be set if get_country is False.
    is_online : boolean, default True
        Whether the machine is connected to the internet or not.
    filepath : str, default .
        Path of the file where all the carbon logs will be written.
    output_format : {'csv', 'excel'}, default 'csv'
        Format of the carbon logs file produced.
    api_endpoint : str, optional
        Endpoint of the API to upload the collected data to

        Note: we provide an endpoint to collect data and contribute, with the
        community, towards greener algorithms.
        Here is the url :
        https://ngji0jx9dc.execute-api.eu-west-3.amazonaws.com/post_new_item

    See Also
    --------
    PowerMeter.from_config : Create a power meter from a config file.

    Examples
    --------
    Create a PowerMeter for the project `MNIST Classifier` while
    not being online.

    >>> power_meter = PowerMeter(project_name="MNIST classifier",
    ...     is_online=False, location="FR")

    Create a PowerMeter for the project `Test` and send the collected data to
    our endpoint.

    >>> power_meter = PowerMeter(project_name="Test",
    ...     api_endpoint="https://ngji0jx9dc.execute-
    api.eu-west-3.amazonaws.com/post_new_item")

    Notes
    -----
    This package may log private data (username, country, project_name).
    If you do not provide any api_endpoint, we will never have access
    to this data.

    On the other hand, if you chose to share your data with us
    (by using our endpoint:
    https://ngji0jx9dc.execute-api.eu-west-3.amazonaws.com/post_new_item
    ), we commit to anonymize any data shared.
    """

    LAPTOP_PUE = 1.3  # pue for my laptop
    SERVER_PUE = 1.58  # pue for a server
    DEFAULT_LOCATION = "FR"
    DATETIME_FORMAT = "%m/%d/%Y %H:%M:%S"  # "%c"

    # ----------------------------------------------------------------------
    # Constructors
    def __init__(
        self,
        project_name="",
        program_name="",
        client_name="",
        user_name="",
        cpu_power_log_path="",
        get_country=True,
        location="",
        is_online=True,
        filepath=None,
        output_format="csv",
        api_endpoint=None,
    ):

        self.platform = sys.platform
        powergadget_platform = {
            "darwin": PowerGadgetMac,
            "win32": PowerGadgetWin,
            "linux": self.__set_powergadget_linux,
            "linux2": self.__set_powergadget_linux,
            "": NoPowerGadget,
        }
        self.power_gadget = powergadget_platform[self.platform](
            powerlog_path=cpu_power_log_path
        )

        self.pue = self.__set_pue()

        self.cuda_available = self.__check_gpu()
        self.gpu_power = self.__set_gpu_power()

        self.user = self.__set_username(user_name)

        self.project = self.__set_project_name(project_name)
        self.program_name = self.__set_project_entity(program_name)
        self.client_name = self.__set_project_entity(client_name)

        self.is_online = is_online
        if api_endpoint:
            LOGGER.info("Api endpoint given, will save data online")
            self.api_endpoint = api_endpoint
        else:
            LOGGER.info("No current api endpoint, will save data locally")
            self.api_endpoint = ""

        self.location = self.__set_location(location, get_country)

        self.energy_mix_db = self.__load_energy_mix_db()
        self.energy_mix = self.__get_energy_mix()  # kgCO2e/kWh
        self.location_name = self.__get_location_name()

        self.used_package = ""
        self.used_algorithm = ""
        self.used_data_type = ""
        self.used_data_shape = ""
        self.used_algorithm_params = ""
        self.used_comments = ""
        self.used_step = ""

        if not filepath:
            LOGGER.info("No current filepath, will use the default")
            self.filepath = Path.cwd() / "emissions.csv"
        else:
            LOGGER.info("Filepath given, will save there")
            self.filepath = Path(filepath)

        self.output_format = output_format

        self.logging_filename = PACKAGE_PATH / LOGGING_FILE

    @staticmethod
    def __load_energy_mix_db():
        return pd.read_csv(
            PACKAGE_PATH / ENERGY_MIX_DATABASE, encoding="utf-8"
        )

    @staticmethod
    def __extract_env_name():
        env = "unknown"
        try:
            env = os.environ["CONDA_DEFAULT_ENV"]
        except KeyError:
            pass
        if hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix:
            env = sys.base_prefix.split("/")[-1]
        return env

    @staticmethod
    def __check_gpu():
        cuda_available = False
        if shutil.which("nvidia-smi"):
            cuda_available = True

        return cuda_available

    @staticmethod
    def __get_country():
        """
        Retrieve the ISO code country
        Beware of the encoding
        cf. from https://stackoverflow.com/questions/40059654/python-convert-
        a-bytes-array-into-json-format
        """
        request = requests.get("http://ipinfo.io/json")
        response = request.content.decode("utf8").replace("'", '"')
        user_info = json.loads(response)
        return user_info["country"]

    @classmethod
    def from_config(cls, path):
        """
        Create a PowerMeter from a json config file.

        The json config file may contain any key named after the arguments of
        the :class:`carbonai.PowerMeter` constructor.

        Parameters
        ----------
        path : str
            Path to the json config file

        Returns
        -------
        PowerMeter

        See also
        --------
        PowerMeter : Instantiate a PowerMeter by declaring every argument

        Examples
        --------
        Example of config file used. This file is named `config.json`

        .. code-block:: JSON

            {
                "project_name": "Project X",
                "program_name": "Program X",
                "client_name": "Client X",
                "get_country": true,
                "is_online": false,
                "user_name": "customUsername",
                "filepath": "",
                "api_endpoint": "...",
                "location":"FR"
            }

        To load this file as a power meter.

        >>> power_meter = PowerMeter.from_config("config.json")
        """
        with open(path) as file:
            args = json.load(file)
        return cls(**args)

    def __set_pue(self):
        if self.platform in ["darwin", "win32"]:
            return self.LAPTOP_PUE  # pue for my laptop
        return self.SERVER_PUE  # pue for a server

    def __set_powergadget_linux(self, powerlog_path=None):
        if POWERLOG_PATH_LINUX.exists():
            power_gadget = PowerGadgetLinuxRAPL()
        # The user needs to be root to use MSR interface
        elif MSR_PATH_LINUX_TEST.exists() and os.getuid() == 0:
            power_gadget = PowerGadgetLinuxMSR()
        else:
            LOGGER.warning("No power reading interface was found")
            power_gadget = NoPowerGadget()
        return power_gadget

    def __set_gpu_power(self):
        if self.cuda_available:
            LOGGER.info("Found a GPU")
            gpu_power = NvidiaPower()
        else:
            LOGGER.info("Found no GPU")
            gpu_power = NoGpuPower()
        return gpu_power

    def __set_username(self, user_name):
        if user_name:
            return user_name
        return getpass.getuser()

    def __set_project_name(self, project_name):
        if project_name:
            return project_name
        return self.__extract_env_name()

    def __set_project_entity(self, entity_name):
        if entity_name:
            return entity_name
        return "--"

    def __set_location(self, provided_location, get_country):
        # Set the location used to convert energy usage to carbon emissions
        # if the location is provided, we use it
        # if it's not and we can use the internet and the user authorize us to
        # #do so then we retrieve it from the IP address
        # otherwise set the location to default
        if provided_location:
            location = provided_location
        elif (self.is_online or self.api_endpoint) and get_country:
            location = self.__get_country()
        else:
            warnings.warn(
                "No location was set, we will fallback to \
                the default location: {}".format(
                    self.DEFAULT_LOCATION
                )
            )
            location = self.DEFAULT_LOCATION
        return location

    def __get_energy_mix(self):
        if not (
            self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location
        ).any():
            raise NameError(
                "The location input was not found, make sure you wrote "
                "the isocode of your country. You used " + self.location
            )
        return self.energy_mix_db.loc[
            self.energy_mix_db[COUNTRY_CODE_COLUMN] == self.location,
            ENERGY_MIX_COLUMN,
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
            cpu_record[TOTAL_ENERGY_PROCESS_CPU]
            + cpu_record[TOTAL_ENERGY_PROCESS_MEMORY]
            + gpu_record[TOTAL_ENERGY_GPU]
        )  # mWh
        co2_emitted = used_energy * self.energy_mix * 1e-3
        LOGGER.info(
            "This process emitted %.3fg of CO2 (using the energy mix of %s)",
            co2_emitted,
            self.location_name,
        )

        return co2_emitted

    def measure_power(
        self,
        package,
        algorithm,
        step="other",
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
            A string describing the package used by this function
            (e.g. sklearn, Pytorch, ...)
        algorithm : str
            A string describing the algorithm used in the function monitored
            (e.g. RandomForestClassifier, ResNet121, ...)
        step : {'inference', 'training', 'other', 'test', 'run', \
            'preprocessing'}, optional
            A string to provide useful information on the current stage
            of the algorithm
        data_type : {'tabular', 'image', 'text', 'time series', 'other'},\
             optional
            A string describing the type of data used for training
        data_shape : str or tuple, optional
            A string or tuple describing the quantity of data used
        algorithm_params : str, optional
            A string describing the parameters used by the algorithm
        comments : str, optional
            A string to provide any useful information

        Returns
        -------

        See also
        --------
        PowerMeter.from_config : Create a PowerMeter object from a config file
        PowerMeter.__call__ : Measure the power usage using a with statement

        Examples
        --------
        First, create a PowerMeter (you only do to this step once).

        >>> power_meter = PowerMeter.from_config("config.json")

        Decorate the function you wish to monitor.

        >>> @power_meter.measure_power(
        ...     package="pandas, numpy",
        ...     algorithm="data cleaning",
        ...     step="preprocessing",
        ...     data_type="tabular",
        ...     comments="Cleaning of csv files + train-test splitting"
        ... )
        ... def example_func():
        ...     # do something

        Each time this function will be called, the PowerMeter will monitor
        the power usage and log the function's carbon footprint.

        >>> example_func()
        result_of_your_function
        """
        if not algorithm or not package:
            raise SyntaxError(
                "Please input a description for the function you are trying "
                "to monitor. Pass in the algorithm and the package you are "
                "trying to monitor"
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
                    step=step,
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
        step="other",
    ):
        self.used_package = normalize(package)
        self.used_algorithm = normalize(algorithm)
        self.used_data_type = normalize(data_type)
        self.used_data_shape = normalize(data_shape)
        self.used_algorithm_params = normalize(algorithm_params)
        self.used_comments = normalize(comments)
        self.used_step = normalize(match(step, AVAILABLE_STEPS))

    def __call__(
        self,
        package,
        algorithm,
        step="other",
        data_type="",
        data_shape="",
        algorithm_params="",
        comments="",
    ):
        """
        Measure the power usage using a with statement.

        Parameters
        ----------
        package : str
            A string describing the package used by this function (e.g.
            sklearn, Pytorch, ...)
        algorithm : str
            A string describing the algorithm used in the function monitored
            (e.g. RandomForestClassifier, ResNet121, ...)
        step : {'inference', 'training', 'other', 'test', 'run', \
            'preprocessing'}, optional
            A string to provide useful information on the current stage
            of the alogrithm
        data_type : {'tabular', 'image', 'text', 'time series', 'other'}, \
            optional
            A string describing the type of data used for training
        data_shape : str or tuple, optional
            A string or tuple describing the quantity of data used
        algorithm_params : str, optional
            A string describing the parameters used by the algorithm
        comments : str, optional
            A string to provide any useful information

        Returns
        -------

        See also
        --------
        PowerMeter.from_config : Create a PowerMeter object from a config file
        PowerMeter.measure_power : Measure the power usage using a function \
            decorator

        Examples
        --------
        First, create a PowerMeter (you only do to this step once).

        >>> power_meter = PowerMeter.from_config("config.json")

        Use a with statement to encapsulate the code you want to monitor

        >>> with power_meter(
        ...     package="pandas, numpy",
        ...     algorithm="data cleaning",
        ...     step="preprocessing",
        ...     data_type="tabular",
        ...     comments="Cleaning of csv files + train-test splitting"
        ... ):
        ...     # do something
        result_of_your_code
        """
        self.__set_used_arguments(
            package,
            algorithm,
            data_type=data_type,
            data_shape=data_shape,
            algorithm_params=algorithm_params,
            comments=comments,
            step=step,
        )
        return self

    def __enter__(
        self,
    ):
        self.start_measure(
            self.used_package,
            self.used_algorithm,
            data_type=self.used_data_type,
            data_shape=self.used_data_shape,
            algorithm_params=self.used_algorithm_params,
            comments=self.used_comments,
        )

    def __exit__(self, exit_type, value, traceback):
        self.stop_measure()

    def start_measure(
        self,
        package,
        algorithm,
        step="other",
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
            A string describing the package used by this function
            (e.g. sklearn, Pytorch, ...)
        algorithm : str
            A string describing the algorithm used in the function monitored
            (e.g. RandomForestClassifier, ResNet121, ...)
        step : {'inference', 'training', 'other', 'test', 'run', \
            'preprocessing'}, optional
            A string to provide useful information on the current stage
            of the algorithm
        data_type : {'tabular', 'image', 'text', 'time series', 'other'},\
            optional
            A string describing the type of data used for training
        data_shape : str or tuple, optional
            A string or tuple describing the quantity of data used
        algorithm_params : str, optional
            A string describing the parameters used by the algorithm
        comments : str, optional
            A string to provide any useful information

        Returns
        -------

        See also
        --------
        PowerMeter.stop_measure : Stop the measure started with start_measure
        PowerMeter.from_config : Create a PowerMeter object from a config file
        PowerMeter.measure_power : Measure the power usage using a function \
            decorator
        PowerMeter.__call__ : Measure the power usage using a with statement

        Notes
        -----
        We do not recommend using this method to monitor the energy usage of
        your code because it won't automatically stop if an error is raised
        at some point while running. You will then have to stop the measure
        manually with :func:`PowerMeter.stop_measure`.

        Examples
        --------
        First, create a PowerMeter (you only do to this step once).

        >>> power_meter = PowerMeter.from_config("config.json")

        Start measuring the code you wish to monitor

        >>> power_meter.start_measure(
        ...     package="pandas, numpy",
        ...     algorithm="data cleaning",
        ...     step="preprocessing",
        ...     data_type="tabular",
        ...     comments="Cleaning of csv files + train-test splitting"
        ... )
        ... # do something
        result_of_your_code

        **Do not forget to stop measuring**

        >>> power_meter.stop_measure()

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
            step=step,
        )

    def stop_measure(self):
        """
        Stops the measure started with :func:`PowerMeter.start_measure`

        Parameters
        ----------

        See also
        --------
        PowerMeter.start_measure : Stop the measure started with start_measure
        PowerMeter.from_config : Create a PowerMeter object from a config file
        PowerMeter.measure_power : Measure the power usage using a function \
            decorator
        PowerMeter.__call__ : Measure the power usage using a with statement

        Notes
        -----
        We do not recommend using this method to monitor the energy usage of
        your code because it won't automatically stop if an error is raised at
        some point while running. You will then have to stop the measure
        manually with :func:`PowerMeter.stop_measure`.

        Examples
        --------
        First, create a PowerMeter (you only do to this step once).

        >>> power_meter = PowerMeter.from_config("config.json")

        Start measuring the code you wish to monitor

        >>> power_meter.start_measure(
        ...     package="pandas, numpy",
        ...     algorithm="data cleaning",
        ...     step="preprocessing",
        ...     data_type="tabular",
        ...     comments="Cleaning of csv files + train-test splitting"
        ... )
        ... # do something
        result_of_your_code

        **Do not forget to stop measuring**

        >>> power_meter.stop_measure()
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
            step=self.used_step,
        )

    def __record_data_to_server(self, info):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(info)
        try:
            response = requests.request(
                "POST",
                self.api_endpoint,
                headers=headers,
                data=data,
                timeout=1,
            )
            return response.status_code
        except requests.exceptions.Timeout:
            return 408

    def __record_data_to_csv_file(self, info):
        try:
            data = pd.DataFrame(info, index=[0])
            if Path(self.filepath).exists():
                data.to_csv(self.filepath, mode="a", index=False, header=False)
            else:
                data.to_csv(self.filepath, index=False)
            return True
        except Exception:
            LOGGER.error("* error during the csv writing process *")
            LOGGER.error(traceback.format_exc())
            return False

    def __record_data_to_excel_file(self, info):
        try:

            if Path(self.filepath).exists():
                data = pd.read_excel(self.filepath).append(
                    info, ignore_index=True
                )
                data.to_excel(self.filepath, index=False)
            else:
                data = pd.DataFrame(info, index=[0])
                data.to_excel(self.filepath, index=False)
            return True
        except Exception:
            LOGGER.error(
                "* error during the writing process in an excel file *"
            )
            LOGGER.error(traceback.format_exc())
            return False

    def __record_data_to_file(self, info):
        """
        Only two options so far: CSV or EXCEL
        """
        if self.filepath.suffix == ".csv":
            return self.__record_data_to_csv_file(info)
        elif self.filepath.suffix == ".xls" or self.filepath.suffix == ".xlsx":
            return self.__record_data_to_excel_file(info)
        LOGGER.info("unknown format: it should be either .csv, .xls or .xlsx")
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
        step="other",
    ):
        co2_emitted = self.__aggregate_power(
            self.power_gadget.record, self.gpu_power.record
        )
        payload = {
            "Datetime": datetime.datetime.now().strftime(self.DATETIME_FORMAT),
            "Country": self.location_name,
            "Platform": self.platform,
            "User ID": self.user,
            "ISO": self.location,
            "Project name": self.project,
            "Program name": self.program_name,
            "Client name": self.client_name,
            "Total Elapsed CPU Time (sec)": cpu_recorded_power[TOTAL_CPU_TIME],
            "Total Elapsed GPU Time (sec)": gpu_recorded_power[TOTAL_GPU_TIME],
            "Cumulative Package Energy (mWh)": cpu_recorded_power[
                TOTAL_ENERGY_ALL
            ],
            "Cumulative IA Energy (mWh)": cpu_recorded_power[TOTAL_ENERGY_CPU],
            "Cumulative GPU Energy (mWh)": gpu_recorded_power[
                TOTAL_ENERGY_GPU
            ],
            "Cumulative DRAM Energy (mWh)": cpu_recorded_power[
                TOTAL_ENERGY_MEMORY
            ],
            "Cumulative process CPU Energy (mWh)": cpu_recorded_power[
                TOTAL_ENERGY_PROCESS_CPU
            ],
            "Cumulative process DRAM Energy (mWh)": cpu_recorded_power[
                TOTAL_ENERGY_PROCESS_MEMORY
            ],
            "PUE": self.pue,
            "CO2 emitted (gCO2e)": co2_emitted,
            "Package": package,
            "Algorithm": algorithm,
            "Algorithm's parameters": algorithm_params,
            "Data type": data_type,
            "Data shape": data_shape,
            "Comment": comments,
            "Step": step,
        }
        written = self.__record_data_to_file(payload)
        LOGGER.info("* recorded into a file? %s*", written)

        if self.is_online and self.api_endpoint:
            response_status_code = self.__record_data_to_server(payload)
            if response_status_code >= 400:
                LOGGER.warning(
                    "We couldn't upload the recorded data to the server, we"
                    "are going to record it for a later upload"
                )
                # can't upload we'll record the data
                data = pd.DataFrame(payload, index=[0])
                if self.logging_filename.exists():
                    data.to_csv(
                        self.logging_filename,
                        mode="a",
                        index=False,
                        header=False,
                    )
                else:
                    data.to_csv(self.logging_filename, index=False)

            if response_status_code == 200:
                # we successfully uploaded,
                # check if there are other locally recorded data
                if self.logging_filename.exists():
                    data = pd.read_csv(self.logging_filename, index_col=None)
                    payloads = data.to_dict(orient="records")
                    for i, payload in enumerate(payloads):
                        res_status_code = self.__record_data_to_server(payload)
                        if res_status_code != 200:
                            data.iloc[i:].to_csv(
                                self.logging_filename, index=False
                            )
                            break
                    else:
                        self.logging_filename.unlink()
