__all__ = ["PowerMeter"]

import json
import requests
import datetime

from PyPowerGadget.PowerGadget import *
from PyPowerGadget.NvidiaPower import *
from PyPowerGadget.settings import *


class PowerMeter:
    def __init__(self, cpu_power_log_path="", get_country=True):
        self.platform = sys.platform
        if self.platform == MAC_PLATFORM:
            self.power_gadget = PowerGadgetMac(power_log_path=cpu_power_log_path)
            self.pue = 1.3  # pue for my laptop
        elif self.platform == WIN_PLATFORM:
            self.power_gadget = PowerGadgetWin(power_log_path=cpu_power_log_path)
            self.pue = 1.3  # pue for my laptop
        elif self.platform == LINUX_PLATFORM:
            self.power_gadget = PowerGadgetLinux(power_log_path=cpu_power_log_path)
            self.pue = 1.58  # pue for a server

        self.cuda_available = self.__check_gpu()
        if self.cuda_available:
            self.gpu_power = NvidiaPower()
        else:
            self.gpu_power = NoGpuPower()

        self.location = "US"
        if get_country:
            self.location = self.__get_country()
        self.energy_mix_db = self.__load_energy_mix_db()
        self.energy_mix = self.__get_energy_mix()  # kgCO2e/kWh
        self.location_name = self.__get_location_name()

        self.logging_filename = PACKAGE_PATH / LOGGING_FILE
        self.logging_columns = [
            "Datetime",
            COUNTRY_CODE_COLUMN,
            COUNTRY_NAME_COLUMN,
            TOTAL_CPU_TIME,
            TOTAL_GPU_TIME,
            TOTAL_ENERGY_ALL,
            TOTAL_ENERGY_CPU,
            TOTAL_ENERGY_GPU,
            TOTAL_ENERGY_MEMORY,
            "PUE",
            "CO2 emitted (gCO2e)",
            "Description",
        ]
        self.__init_logging_file()

    def __load_energy_mix_db(self):
        return pd.read_csv(PACKAGE_PATH / ENERGY_MIX_DATABASE)

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

    def aggregate_power(self, cpu_recorded_power, gpu_recorded_power):
        # print(pd.concat([cpu_recorded_power, gpu_recorded_power]))

        used_energy = self.pue * (
            cpu_recorded_power[TOTAL_ENERGY_CPU]
            + cpu_recorded_power[TOTAL_ENERGY_MEMORY]
            + gpu_recorded_power[TOTAL_ENERGY_GPU]
        )  # mWh
        co2_emitted = used_energy * self.energy_mix * 1e-3
        print(
            "This process emitted %.3fg of CO2 (using the energy mix of %s)"
            % (co2_emitted, self.location)
        )

        return co2_emitted

    def mesure_power(self, func, description="", time_interval=1):
        def wrapper(*args, **kwargs):
            self.gpu_power.start_mesure()
            try:
                results = self.power_gadget.wrapper(
                    func, *args, time_interval=time_interval, **kwargs
                )
            finally:
                self.gpu_power.stop_mesure()
                self.gpu_power.parse_power_log()
            self.log_records(
                self.power_gadget.recorded_power,
                self.gpu_power.recorded_power,
                description=description,
            )
            return results

        return wrapper

    def __init_logging_file(self):
        if not self.logging_filename.exists():
            self.logging_filename.write_text(",".join(self.logging_columns))

    def log_records(self, cpu_recorded_power, gpu_recorded_power, description=""):
        co2_emitted = self.aggregate_power(
            self.power_gadget.recorded_power, self.gpu_power.recorded_power
        )
        info = [
            str(datetime.datetime.now()),
            self.location,
            self.location_name,
            str(cpu_recorded_power[TOTAL_CPU_TIME]),
            str(gpu_recorded_power[TOTAL_GPU_TIME]),
            str(cpu_recorded_power[TOTAL_ENERGY_ALL]),
            str(cpu_recorded_power[TOTAL_ENERGY_CPU]),
            str(gpu_recorded_power[TOTAL_ENERGY_GPU]),
            str(cpu_recorded_power[TOTAL_ENERGY_MEMORY]),
            str(self.pue),
            str(co2_emitted),
            description.replace(",", ";"),
        ]
        self.logging_filename.open("a").write("\n" + (",".join(info)))
