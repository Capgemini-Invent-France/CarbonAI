.. _installation:

============
Installation
============
This package is compatible with most platforms with varying installation processes

Mac
-----
To use this package you will need to install the Intel Power Gadget driver and tool.
The easiest may be using brew:
``brew cask install intel-power-gadget``
You can also find it here: https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html

   | intel-power-gadget requires a kernel extension to work. If the installation fails, retry after you enable it in: `System Preferences → Security & Privacy → General`
   | For more information, refer to vendor documentation or this Apple Technical Note: https://developer.apple.com/library/content/technotes/tn2459/_index.html

You can now head to the `All platforms`_ section

Windows
-------
To use this package you will need to install the Intel Power Gadget driver and tool.
You can find it here: https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html

You can now head to the `All platforms`_ section


Ubuntu
------
If you're on Ubuntu, no need to perform any software installation. 
Make sure, any of the following command works :
Either this works : ``ls /sys/class/powercap/intel-rapl/intel-rapl:*/``
or you need to enable the MSR using ``modprobe msr`` and you will need to execute your code as root

You can now head to the `All platforms`_ section


All platforms
-------------
Once you've installed (if needed) the intel power gadget.
Install the package using pip :
``pip install carbonai``
