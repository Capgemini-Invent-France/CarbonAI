from pathlib import Path
import os

PACKAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = Path.home()

DMG_PATH = Path("/tmp/IntelPowerGadget.dmg")
MSI_PATH = Path("C:\\tmp\\IntelPowerGadget.msi")

POWERLOG_PATH_MAC = Path("/Applications/Intel Power Gadget/PowerLog")
POWERLOG_PATH_WIN = Path("/Program Files/Intel/Power Gadget 3.5")
POWERLOG_TOOL_WIN = "IntelPowerGadget.exe"
POWERLOG_PATH_LINUX = Path("/sys/class/powercap/intel-rapl")

ENERGY_MIX_DATABASE = Path("ademe_energy_mix_by_country.csv")
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

API_ENDPOINT = (
    "https://50esc1hzja.execute-api.eu-west-3.amazonaws.com/green-ai-db-handling"
)
