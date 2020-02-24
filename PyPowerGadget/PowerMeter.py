__all__ = ["PowerMeter"]

import json
import requests

from PyPowerGadget.PowerGadget import *
from PyPowerGadget.NvidiaPower import *
from PyPowerGadget.settings import *


class PowerMeter:
    def __init__(self, cpu_power_log_path="", get_country=False):
        self.platform = sys.platform
        if self.platform == MAC_PLATFORM:
            self.power_gadget = PowerGadgetMac(power_log_path=cpu_power_log_path)
        elif self.platform == WIN_PLATFORM:
            self.power_gadget = PowerGadgetWin(power_log_path=cpu_power_log_path)
        elif self.platform == LINUX_PLATFORM:
            self.power_gadget = PowerGadgetLinux(power_log_path=cpu_power_log_path)

        self.cuda_available = self.__check_gpu()
        if self.cuda_available:
            self.gpu_power = NvidiaPower()
        else:
            self.gpu_power = NoGpuPower()
        self.pue = 1.28  # pue for my laptop
        # self.pue = 1.58 # pue for a server
        self.location = "USA"
        if get_country:
            self.location = self.__get_country()
        self.energy_mix = 0.522  # kgCO2e/kWh

    def __get_country(self):
        # from https://stackoverflow.com/questions/40059654/python-convert-a-bytes-array-into-json-format
        r = requests.get("http://ipinfo.io/json")
        response = r.content.decode("utf8").replace("'", '"')
        user_info = json.loads(response)
        return user_info["country"]

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
        print(pd.concat([cpu_recorded_power, gpu_recorded_power]))
        # print(gpu_recorded_power)

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

    def mesure_power(self, func, time_interval=1):
        def wrapper(*args, **kwargs):
            self.gpu_power.start_mesure()
            try:
                results = self.power_gadget.wrapper(
                    func, *args, time_interval=time_interval, **kwargs
                )
            finally:
                self.gpu_power.stop_mesure()
                self.gpu_power.parse_power_log()
            self.aggregate_power(
                self.power_gadget.recorded_power, self.gpu_power.recorded_power
            )
            return results

        return wrapper
