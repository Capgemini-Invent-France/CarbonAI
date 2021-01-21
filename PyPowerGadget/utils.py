from pathlib import Path
import os

import pandas as pd

PACKAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = Path.home()

ENERGY_MIX_DATABASE = Path("data/ademe_energy_mix_by_country.csv")
ENERGY_MIX_COLUMN = "Energy mix (kgCO2/kWh)"
COUNTRY_CODE_COLUMN = "ISO"
COUNTRY_NAME_COLUMN = "Country"

MAC_PLATFORM = "darwin"
WIN_PLATFORM = "win32"
LINUX_PLATFORMS = ["linux", "linux2"]
MAC_INTELPOWERLOG_FILENAME = "intelPowerLog.csv"
WIN_INTELPOWERLOG_FILENAME = "PwrData_*.csv"

LOGGING_FILE = "power_logs.csv"

TOTAL_CPU_TIME = "Total Elapsed CPU Time (sec)"
TOTAL_GPU_TIME = "Total Elapsed GPU Time (sec)"
TOTAL_ENERGY_ALL = "Cumulative Package Energy (mWh)"
TOTAL_ENERGY_CPU = "Cumulative IA Energy (mWh)"
TOTAL_ENERGY_GPU = "Cumulative GPU Energy (mWh)"
TOTAL_ENERGY_MEMORY = "Cumulative DRAM Energy (mWh)"


def get_logged_data():
    return pd.read_csv(PACKAGE_PATH / LOGGING_FILE, encoding="utf-8")


def save_logged_data(path):
    df = get_logged_data()
    df.to_csv(path)
