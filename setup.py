from setuptools import setup, find_packages

from setuptools.command.install import install

import re


def get_property(prop, project):
    result = re.search(
        r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project).read())
    return result.group(1)


setup(
    name="CarbonAImpact",
    version=get_property("__version__", 'CarbonAImpact/version.py'),
    description="Monitor the power consumption of a function",
    author="Capgemini Invent - Martin Chauvin, Francois Lemeille, Jordan Toh",
    package_data={"": ["data/ademe_energy_mix_by_country.csv"]},
    packages=find_packages(),
    python_requires=">=3.*, <4",
    install_requires=["pandas", "numpy", "requests", "ipython", "fuzzywuzzy"],
    license="MIT",
)
