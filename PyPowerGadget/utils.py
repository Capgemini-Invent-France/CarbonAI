from pathlib import Path
import os

import pandas as pd

PACKAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = Path.home()

DMG_PATH = Path("/tmp/IntelPowerGadget.dmg")
MSI_PATH = Path("C:\\tmp\\IntelPowerGadget.msi")

POWERLOG_PATH_MAC = Path("/Applications/Intel Power Gadget/PowerLog")
POWERLOG_PATH_WIN = Path("/Program Files/Intel/Power Gadget 3.5")
POWERLOG_TOOL_WIN = "IntelPowerGadget.exe"
POWERLOG_PATH_LINUX = Path("/sys/class/powercap/intel-rapl")

CPU_IDS_DIR = "/sys/devices/system/cpu/cpu*/topology/physical_package_id"
READ_MSR_PATH = "/dev/cpu/{}/msr"
READ_RAPL_PATH = "/sys/class/powercap/intel-rapl/intel-rapl:{}/" #rapl_socket_id
RAPL_DEVICENAME_FILE = "name"
RAPL_ENERGY_FILE = "energy_uj"
RAPL_DRAM_PATH = "intel-rapl:{}:{}/" #rapl_socket_id, rapl_device_id


ENERGY_MIX_DATABASE = Path("data/ademe_energy_mix_by_country.csv")
ENERGY_MIX_COLUMN = "Energy mix (kgCO2/kWh)"
COUNTRY_CODE_COLUMN = "ISO"
COUNTRY_NAME_COLUMN = "Country"

MAC_PLATFORM = "darwin"
WIN_PLATFORM = "win32"
LINUX_PLATFORMS = ["linux", "linux2"]
MAC_INTELPOWERLOG_FILENAME = "intelPowerLog.csv"
WIN_INTELPOWERLOG_FILENAME = "PwrData_*.csv"
NVIDIAPOWERLOG_FILENAME = "nvidiaPowerLog.csv"

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
