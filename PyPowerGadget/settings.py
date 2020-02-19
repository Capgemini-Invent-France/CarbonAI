from pathlib import Path


DMG_PATH = Path("/tmp/IntelPowerGadget.dmg")
MSI_PATH = Path("C:\\tmp\\IntelPowerGadget.msi")

POWERLOG_PATH_MAC = Path("/Applications/Intel Power Gadget/PowerLog")
POWERLOG_PATH_WIN = Path("C:\\Program Files\\Intel\\Power Gadget 3.5\\PowerLog3.0.exe")
MAC_PLATFORM = "darwin"
WIN_PLATFORM = "win32"
LINUX_PLATFORM = "linux"
# PROJECT_PATH = "/Users/martinchauvin/Capgemini/Green AI - General/green_ai_code/"
INTELPOWERLOG_FILENAME = "intelPowerLog.csv"
NVIDIAPOWERLOG_FILENAME = "nvidiaPowerLog.csv"


TOTAL_TIME = "Total Elapsed Time (sec)"
TOTAL_ENERGY_ALL = "Cumulative Package Energy (mWh)"
TOTAL_ENERGY_CPU = "Cumulative IA Energy (mWh)"
TOTAL_ENERGY_GPU = "Cumulative GPU Energy (mWh)"
TOTAL_ENERGY_MEMORY = "Cumulative DRAM Energy (mWh)"
