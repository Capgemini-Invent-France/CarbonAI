__all__ = ["mesure_power"]

import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

from PyPowerGadget.PowerGadget import *
from PyPowerGadget.settings import *


# def extract_model(func):
#     """
#     Look for the tag "# model" in the function code and extract the function below
#     """
#     source = inspect.getsource(func)
#     return "=".join(
#         re.search("(?<=(# classifier\\n))(.*?)(?=\\n)", source).group(0).split("=")[1:]
#     )


def extract_power(list_of_power, interval=1):
    list_of_power.append(get_power_consumption(duration=interval))
    while True:
        list_of_power.append(get_power_consumption(duration=interval))


def execute_function(fun, fun_args, results):
    results["results"] = fun(*fun_args[0], **fun_args[1])


def aggregate_power(recorded_power):
    summary = recorded_power.sum(axis=0)
    pue = 1.28  # pue for my laptop
    # pue = 1.58 # pue for a server
    print(summary)
    used_energy = pue * (summary[TOTAL_ENERGY_CPU] + summary[TOTAL_ENERGY_MEMORY])


def mesure_power(func, time_interval=1, model_name=False):
    import pandas as pd
    import time
    import multiprocessing
    from multiprocessing import Process, Manager

    def wrapper(*args, **kwargs):
        multiprocessing.set_start_method("spawn", force=True)
        with Manager() as manager:
            power_draws = manager.list()
            return_dict = manager.dict()

            func_process = Process(
                target=execute_function, args=(func, (args, kwargs), return_dict)
            )
            power_process = Process(
                target=extract_power, args=(power_draws, time_interval)
            )

            power_process.start()
            func_process.start()

            func_process.join()
            power_process.terminate()
            power_process.join()

            power_draws_list = list(power_draws)
            time.sleep(2)
            # power_draws_list.append(parse_power_log())
            results = return_dict["results"]
        aggregate_power(pd.DataFrame.from_records(power_draws_list))
        return results

    return wrapper


def say_whee():
    import time

    time.sleep(11)
    print("Whee!")
    return


if __name__ == "__main__":
    power_gadget = PowerGadget()
    print(power_gadget.mesure_power(say_whee)())
