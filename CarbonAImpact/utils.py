from pathlib import Path
import os

PACKAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
HOME_DIR = Path.home()

ENERGY_MIX_DATABASE = Path("data/ademe_energy_mix_by_country.csv")
ENERGY_MIX_COLUMN = "Energy mix (kgCO2/kWh)"
COUNTRY_CODE_COLUMN = "ISO"
COUNTRY_NAME_COLUMN = "Country"

POWERLOG_PATH_LINUX = Path("/sys/class/powercap/intel-rapl")
MAC_INTELPOWERLOG_FILENAME = "intelPowerLog.csv"
WIN_INTELPOWERLOG_FILENAME = "PwrData_*.csv"

LOGGING_FILE = "power_logs.csv"

TOTAL_CPU_TIME = "Total Elapsed CPU Time (sec)"
TOTAL_GPU_TIME = "Total Elapsed GPU Time (sec)"
TOTAL_ENERGY_ALL = "Cumulative Package Energy (mWh)"
TOTAL_ENERGY_CPU = "Cumulative IA Energy (mWh)"
TOTAL_ENERGY_GPU = "Cumulative GPU Energy (mWh)"
TOTAL_ENERGY_MEMORY = "Cumulative DRAM Energy (mWh)"

AVAILABLE_STEPS = ['inference', 'training', 'other', 'test', 'run', 'preprocessing']

def match(s, options, threshold=80):
    """ """
    from fuzzywuzzy import fuzz
    results = ( (opt, fuzz.token_set_ratio(opt.lower(), s.lower())) for opt in options )
    results = sorted([(opt, v) for opt,v in results if v >= threshold], key=lambda tupl: tupl[1], reverse=True)
    if results:
        return results[0][0]
    else:
        return s

def normalize(s, default_value=""):
    """ """
    return str(s).lower() if s else default_value.lower()