#
# This file is part of Dragonfly.
# (c) Copyright 2007, 2008 by Christo Butcher
# Licensed under the LGPL.
#
#   Dragonfly is free software: you can redistribute it and/or modify it 
#   under the terms of the GNU Lesser General Public License as published 
#   by the Free Software Foundation, either version 3 of the License, or 
#   (at your option) any later version.
#
#   Dragonfly is distributed in the hope that it will be useful, but 
#   WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public 
#   License along with Dragonfly.  If not, see 
#   <http://www.gnu.org/licenses/>.
#

"""
Test cases for the logging framework
============================================================================

"""

import sys
import logging
import logging.handlers
import unittest
import dragonfly.log as log
from dragonfly import *


#===========================================================================

class OutputCapturer(object):

    def __init__(self):
        self.blocks = []

    def write(self, data):
        self.blocks.append(data)

    def flush(self):
        pass

    def clear(self):
        self.blocks = []

    @property
    def lines(self, prefix=""):
        if not self.blocks:
            return ()
        else:
            text = "".join(self.blocks).splitlines()
            text = prefix + ("\n" + prefix).join(text)
            return text.splitlines()


#---------------------------------------------------------------------------

class LogTestCase(unittest.TestCase):
    """
    """

    def setUp(self):
        self._original_stdout = sys.stdout
        self._output = OutputCapturer()
        sys.stdout = self._output
        self._original_stderr = sys.stderr
        self._error = OutputCapturer()
        sys.stderr = self._error

    def tearDown(self):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        if self._output.blocks:
            prefix = "Output:  "
            output = "".join(self._output.blocks).splitlines()
            output = prefix + ("\n" + prefix).join(output)
            print output
        if self._error.blocks:
            prefix = "Error:   "
            text = "".join(self._error.blocks).splitlines()
            text = prefix + ("\n" + prefix).join(text)
            print text
        self._output = None
        self._error = None

    def test_absence_of_no_handlers_error(self):
        """ Verify that the "No handlers could be found" error is not given. """
        log.setup_log()
        logger = get_log("test.log")
        logger.error("test_absence_of_no_handlers_error")
        for line in self._error.lines:
            if line.startswith("No handlers could be found for logger"):
                self.fail("Unexpected error message: %r" % line)

    def test_library_prefix(self):
        """ Verify that loggers have the correct prefix. """
        expected_prefix = "%s.test.log: " % log.library_prefix
        log.setup_log()
        logger = get_log("test.log")
        logger.error("test_library_prefix")
        for line in self._output.lines:
            if line.startswith(expected_prefix):
                return
        self.fail("Logger prefix is incorrect.")

    def test_filtering(self):
        """ Verify that ... """
        log.setup_log()#use_file=False)
        logger = get_log("grammar")
        logger.debug("test_filtering - debug")
        logger.info("test_filtering - info")
        logger.warning("test_filtering - warning")
        logger.error("test_filtering - error")
        logger = get_log("grammar.begin")
        logger.debug("test_filtering - debug")
        logger.info("test_filtering - info")
        logger.warning("test_filtering - warning")
        logger.error("test_filtering - error")
        logger = get_log("grammar.load")
        logger.debug("test_filtering - debug")
        logger.info("test_filtering - info")
        logger.warning("test_filtering - warning")
        logger.error("test_filtering - error")

    def test_set_log_level(self):
        """ Verify that ... """
        log.setup_log()#use_file=False)
        logger = get_log("test.log")

        self._output.clear()
        set_log_level("test.log", logging.WARNING)
        logger.debug("test_set_log_level - debug")
        logger.info("test_set_log_level - info")
        logger.warning("test_set_log_level - warning")
        assert len(self._output.lines) == 1

        self._output.clear()
        set_log_level("test.log", logging.INFO)
        logger.debug("test_set_log_level - debug")
        logger.info("test_set_log_level - info")
        logger.warning("test_set_log_level - warning")
        assert len(self._output.lines) == 2

        self._output.clear()
        set_log_level("test.log", logging.DEBUG)
        logger.debug("test_set_log_level - debug")
        logger.info("test_set_log_level - info")
        logger.warning("test_set_log_level - warning")
        assert len(self._output.lines) == 3

        self._output.clear()
        set_log_level("test.log", logging.ERROR)
        logger.debug("test_set_log_level - debug")
        logger.info("test_set_log_level - info")
        logger.warning("test_set_log_level - warning")
        assert not self._output.lines

    def _new_lines(self):
        filename = None
        if not hasattr(self, "_previous_line_count"):
            self._previous_line_count = 0
        lines = open(filename).readlines()
        new_lines = lines[self._previous_line_count:]
        self._previous_line_count = len(lines)
        return new_lines

    def test_file_output(self):
        """ Verify that ... """
        log.setup_log()
        logger = get_log("test.log")

        self._output.clear()
        set_log_level("test.log", logging.WARNING)
        logger.debug("test_set_log_level - debug")
        logger.info("test_set_log_level - info")
        logger.warning("test_set_log_level - warning")
        assert len(self._output.lines) == 1


#===========================================================================

if __name__ == "__main__":
    unittest.main()
