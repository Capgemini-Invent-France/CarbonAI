__all__ = ["get_logged_data", "save_logged_data"]

import pandas as pd

from PyPowerGadget.settings import *


def get_logged_data():
    return pd.read_csv(PACKAGE_PATH / LOGGING_FILE, encoding="utf-8")


def save_logged_data(path):
    df = get_logged_data()
    df.to_csv(path)
