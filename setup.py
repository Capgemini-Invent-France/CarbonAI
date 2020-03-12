from setuptools import setup, find_packages

from setuptools.command.install import install


setup(
    name="PyPowerGadget",
    version="0.0.3.1",
    description="Monitor the power consumption of a function",
    author="Neyri",
    package_data={"": ["ademe_energy_mix_by_country.csv"]},
    packages=find_packages(),
    python_requires=">=3.*, <4",
    install_requires=["pandas", "numpy", "requests"],
    license="MIT",
)
