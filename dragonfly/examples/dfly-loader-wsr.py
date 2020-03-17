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
directory it's in and loads any ``_*.py`` it finds.

"""

import os.path
import sys

import six

from dragonfly import get_engine
from dragonfly.loader import CommandModuleDirectory
from dragonfly.log import setup_log

#---------------------------------------------------------------------------
# Set up basic logging.

setup_log()
# logging.getLogger("compound.parse").setLevel(logging.INFO)


#---------------------------------------------------------------------------
# Main event driving loop.

def main():
    try:
        path = os.path.dirname(__file__)
    except NameError:
        # The "__file__" name is not always available, for example
        #  when this module is run from PythonWin.  In this case we
        #  simply use the current working directory.
        path = os.getcwd()
        __file__ = os.path.join(path, "dfly-loader-wsr.py")

    # Initialize and connect the engine.
    # Set any configuration options here as keyword arguments.
    engine = get_engine("sapi5inproc")
    engine.connect()

    # Load grammars.
    directory = CommandModuleDirectory(path, excludes=[__file__])
    directory.load()

    # Define recognition callback functions.
    def on_begin():
        print("Speech start detected.")

    def on_recognition(words):
        message = u"Recognized: %s" % u" ".join(words)

        # This only seems to be an issue with Python 2.7 on Windows.
        if six.PY2:
            encoding = sys.stdout.encoding or "ascii"
            message = message.encode(encoding, errors='replace')
        print(message)

    def on_failure():
        print("Sorry, what was that?")

    # Recognize from WSR in a loop.
    try:
        engine.do_recognition(on_begin, on_recognition, on_failure)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
