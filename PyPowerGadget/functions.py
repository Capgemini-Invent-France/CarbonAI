__all__ = ["get_logged_data"]

import pandas as pd

from PyPowerGadget.settings import *


def get_logged_data():
    return pd.read_csv(PACKAGE_PATH/LOGGING_FILE)
