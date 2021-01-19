from setuptools import setup, find_packages

from setuptools.command.install import install

import re

def get_property(prop, project):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project).read())
    return result.group(1)

setup(
    name="PyPowerGadget",
    version=get_property("__version__", 'PyPowerGadget/version.py'),
    description="Monitor the power consumption of a function",
    author="Neyri",
    package_data={"": ["ademe_energy_mix_by_country.csv"]},
    packages=find_packages(),
    python_requires=">=3.*, <4",
    install_requires=["pandas", "numpy", "requests", "ipython"],
    license="MIT",
)
