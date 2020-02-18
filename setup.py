from setuptools import setup, find_packages

from setuptools.command.install import install


setup(
    name="PyPowerGadget",
    version="0.0.2",
    description="Monitor the power consumption of a function",
    author="Neyri",
    packages=find_packages(),
    python_requires=">=3.*, <4",
    install_requires=["pandas", "numpy"],
    license="MIT",
)
