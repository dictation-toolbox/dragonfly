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


import unittest
import time
import logging
from dragonfly.engines import get_engine


#===========================================================================

class CapturingHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []

    def emit(self, record):
        self.records.append(record)


#===========================================================================

class TestTimer(unittest.TestCase):

    def setUp(self):
        self.log_capture = CapturingHandler()
        logging.getLogger("engine.timer").addHandler(self.log_capture)
        self.engine = get_engine()

    def test_timer_callback_exception(self):
        """ Test handling of exceptions during timer callback. """

        callback_called = [0]
        def callback():
            callback_called[0] += 1
            raise Exception("Exception from timer callback")

        interval = 0.01
        timer = self.engine.create_timer(callback, interval)
        timer.manager.main_callback()
        time.sleep(0.02)
        timer.manager.main_callback()

        self.assertEqual(callback_called, [1])
        self.assertEqual(len(self.log_capture.records), 1)
        log_message = self.log_capture.records[0].msg
        self.assertTrue("Exception from timer callback" in log_message)

#===========================================================================

if __name__ == "__main__":
    unittest.main()
