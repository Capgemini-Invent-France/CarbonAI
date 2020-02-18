from setuptools import setup, find_packages

from setuptools.command.install import install


# class InstallIntelPowerGadget(install):
#     def run(self):
#         import sys
#         import requests
#         import PyPowerGadget.settings as settings
#         import subprocess
#         import os
#
#         platform = sys.platform
#
#         if platform == "darwin":
#             r = requests.get(
#                 "https://software.intel.com/sites/default/files/managed/91/6b/Intel%20Power%20Gadget.dmg",
#                 allow_redirects=True,
#             )
#             with open(settings.DMG_PATH, "wb") as dmg_file:
#                 dmg_file.write(r.content)
#             subprocess.call(
#                 "hdiutil attach -mountpoint /tmp/intel " + settings.DMG_PATH
#             )
#             subprocess.call("open", "/tmp/intel/Install Intel Power Gadget.pkg")
#
#             assert "PowerLog" in os.listdir(settings.POWERLOG_PATH)
#         elif platform == "win32":
#             r = requests.get(
#                 "https://software.intel.com/file/823776/download", allow_redirects=True
#             )
#             with open(settings.MSI_PATH, "wb") as msi_file:
#                 msi_file.write(r.content)
#             subprocess.call("msiexec /i %s /qn" % settings.MSI_PATH)


setup(
    name="PyPowerGadget",
    version="0.0.2",
    description="Monitor the power consumption of a function",
    author="Neyri",
    packages=find_packages(),
    python_requires=">=3.*, <4",
    install_requires=["pandas", "numpy"],
    license="MIT",
    # cmdclass={"install": InstallIntelPowerGadget},
)
