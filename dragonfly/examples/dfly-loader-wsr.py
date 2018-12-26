#
# This file is a command-module for Dragonfly.
# (c) Copyright 2008 by Christo Butcher
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>
#

"""
Command-module loader for WSR
=============================

This script can be used to look Dragonfly command-modules 
for use with Window Speech Recognition.  It scans the 
directory it's in and loads any ``*.py`` it finds.

"""


import time
import os.path
import logging
import pythoncom

from dragonfly.engines.backend_sapi5.engine import Sapi5InProcEngine
from dragonfly.loader import CommandModuleDirectory


#---------------------------------------------------------------------------
# Set up basic logging.

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("compound.parse").setLevel(logging.INFO)


#---------------------------------------------------------------------------
# Main event driving loop.

def main():
    logging.basicConfig(level=logging.INFO)

    try:
        path = os.path.dirname(__file__)
    except NameError:
        # The "__file__" name is not always available, for example
        #  when this module is run from PythonWin.  In this case we
        #  simply use the current working directory.
        path = os.getcwd()
        __file__ = os.path.join(path, "dfly-loader-wsr.py")

    engine = Sapi5InProcEngine()
    engine.connect()

    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    engine.speak('beginning loop!')
    while 1:
        pythoncom.PumpWaitingMessages()
        time.sleep(.1)

if __name__ == "__main__":
    main()
