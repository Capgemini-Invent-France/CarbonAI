__all__ = ["PowerMeter"]


from PyPowerGadget.PowerGadget import *
from PyPowerGadget.NvidiaPower import *
from PyPowerGadget.settings import *

class PowerMeter():
    def __init__(self, cpu_power_log_path=""):
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

    def __check_gpu(self):
        import ctypes
        libnames = ('libcuda.so', 'libcuda.dylib', 'cuda.dll')
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
        print(cpu_recorded_power)
        print(gpu_recorded_power)

        used_energy = self.pue * (cpu_recorded_power[TOTAL_ENERGY_CPU] + cpu_recorded_power[TOTAL_ENERGY_MEMORY]+gpu_recorded_power[TOTAL_ENERGY_GPU]) #mWh
        print(used_energy)

    def mesure_power(self, func, time_interval=1):

        def wrapper(*args, **kwargs):
            self.gpu_power.start_mesure()
            try :
                results = self.power_gadget.wrapper(func, *args, time_interval=time_interval, **kwargs)
            finally :
                self.gpu_power.stop_mesure()
                self.gpu_power.parse_power_log()
            self.aggregate_power(self.power_gadget.recorded_power, self.gpu_power.recorded_power)
            return results

        return wrapper
