import os
from pathlib import Path

from fuzzywuzzy import fuzz  # type: ignore

PACKAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = Path.home()

ENERGY_MIX_DATABASE = Path("data/ademe_energy_mix_by_country.csv")
ENERGY_MIX_COLUMN = "Energy mix (kgCO2/kWh)"
COUNTRY_CODE_COLUMN = "ISO"
COUNTRY_NAME_COLUMN = "Country"

POWERLOG_PATH_LINUX = Path("/sys/class/powercap/intel-rapl")
MSR_PATH_LINUX_TEST = Path("/dev/cpu/0/msr")
MAC_INTELPOWERLOG_FILENAME = "intelPowerLog.csv"
WIN_INTELPOWERLOG_FILENAME = "PwrData_*.csv"

LOGGING_FILE = "power_logs.csv"

TOTAL_CPU_TIME = "Total Elapsed CPU Time (sec)"
TOTAL_GPU_TIME = "Total Elapsed GPU Time (sec)"
TOTAL_ENERGY_ALL = "Cumulative Package Energy (mWh)"
TOTAL_ENERGY_CPU = "Cumulative IA Energy (mWh)"
TOTAL_ENERGY_PROCESS_CPU = "Cumulative process CPU Energy (mWh)"
TOTAL_ENERGY_GPU = "Cumulative GPU Energy (mWh)"
TOTAL_ENERGY_MEMORY = "Cumulative DRAM Energy (mWh)"
TOTAL_ENERGY_PROCESS_MEMORY = "Cumulative process DRAM Energy (mWh)"
CPU_PERCENT_USAGE = "CPU_percent_usage"
MEMORY_PERCENT_USAGE = "memory_percent_usage"

AVAILABLE_STEPS = [
    "inference",
    "training",
    "other",
    "test",
    "run",
    "preprocessing",
]


def match(s, options, threshold=80):
    """Fuzzy matching function."""

    results = (
        (opt, fuzz.token_set_ratio(opt.lower(), s.lower())) for opt in options
    )
    results = sorted(
        [(opt, v) for opt, v in results if v >= threshold],
        key=lambda tupl: tupl[1],
        reverse=True,
    )
    if results:
        return results[0][0]

    return s


def normalize(normalize_s, default_value=""):
    """Normalization function.

    Args:
        normalize_s (str): string to normalize.
        default_value (str, optional): [description]. Defaults to "".

    Returns:
        [type]: [description]
    """
    return str(normalize_s).lower() if normalize_s else default_value.lower()
