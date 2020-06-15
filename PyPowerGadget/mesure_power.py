import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))

from PyPowerGadget.PowerMeter import *
from PyPowerGadget.settings import *
import time

power_meter = PowerMeter(project_name="Test measure power")


@power_meter.measure_power(algorithm="classic python", package="None")
def say_whee():

    # for i in range(11):
    time.sleep(31)
    print("Whee!")
    # raise "test"
    return


# import datetime
# import json
# import requests
# import pandas as pd
#
# payload = {
#     "Datetime": str(datetime.datetime(2020, 6, 8, 18, 43, 13, 237197)),
#     "Country": "France",
#     "Platform": "darwin",
#     "User ID": "martinchauvin",
#     "ISO": "FR",
#     "Project name": "Test measure power",
#     "Total Elapsed CPU Time (sec)": 12.108349,
#     "Total Elapsed GPU Time (sec)": 0,
#     "Cumulative Package Energy (mWh)": 9.496732,
#     "Cumulative IA Energy (mWh)": 5.588209,
#     "Cumulative GPU Energy (mWh)": 0,
#     "Cumulative DRAM Energy (mWh)": 2.760008,
#     "PUE": 1.3,
#     "CO2 emitted (gCO2e)": 0.0008584471541100001,
#     "Package": "None",
#     "Algorithm": "classic python",
#     "Algorithm's parameters": "",
#     "Data type": "",
#     "Data shape": "(15,3)",
#     "Comment": "",
# }
# data = pd.read_csv('power_logs.csv', index_col=None)
# data = data[data.columns[7:]]
# data.to_csv('power_logs.csv', index=False)
# data.to_dict(orient='records')
# data.to_csv('test.csv')
#
# headers = {"Content-Type": "application/json"}
# print(payload)
# payload = json.dumps(payload)
# response = requests.request(
#     "POST",
#     "https://50esc1hzja.execute-api.eu-west-3.amazonaws.com/green-ai-db-handling",
#     headers=headers,
#     data=payload,
# )
# response

if __name__ == "__main__":
    print(say_whee())

    # a notebook like program
    power_meter.start_measure(algorithm="classic python", package="None")
    time.sleep(11)
    print("Whee!")
    # raise "test"
    power_meter.stop_measure()

    with power_meter(algorithm="classic python", package="None") as p_m:
        time.sleep(11)
        print("Whee!")
