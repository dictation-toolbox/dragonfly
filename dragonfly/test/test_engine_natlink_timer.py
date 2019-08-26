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
Test cases for the Natlink timer
============================================================================

"""

import unittest


#---------------------------------------------------------------------------

class NatlinkTimerManagerTest(unittest.TestCase):
    """ NatlinkTimerManager tests. """

    def DISABLED_test_natlink_timer_manager(self):
        return

        import dragonfly.engines.backend_natlink as backend
        print(backend.is_engine_available())
        engine = backend.get_engine()
        print(engine)
        engine.connect()
        try:
            print("starting timer...")
            def callback():
                engine._log.error("timer callback")
                print("timer callback")
            timer = engine.create_timer(callback, 1)
            print("timer:", timer)

            print("starting Luke...")
            import sys
            import time
            import win32gui
            timeout = time.time() + 3
            while time.time() < timeout:
                print("Luke")
                sys.stdout.flush()
                if win32gui.PumpWaitingMessages():
                    raise RuntimeError("We got an unexpected WM_QUIT message!")
                time.sleep(1)

        finally:
            engine.disconnect()

#        self.engine.natlink.setTimerCallback(callback, int(sec * 1000))


#---------------------------------------------------------------------------

class NatlinkTimerTest(object):#unittest.TestCase):
    """ Natlink timer tests. """

    def DISABLED_test_natlink_timer(self):
        return

        callback_occurred = False
        def callback():
            callback_occurred = True
        ticks = 200

        import time
        import natlink
        natlink.natConnect()
        try:
            natlink.setTimerCallback(callback, ticks)
#            time.sleep(1)
            import sys
            import time
            import win32gui
            timeout = time.time() + 3
            while time.time() < timeout:
                print("Luke")
                sys.stdout.flush()
                if win32gui.PumpWaitingMessages():
                    raise RuntimeError("We got an unexpected WM_QUIT message!")
                time.sleep(1)
            natlink.setTimerCallback(None, 0)
            print("callback occurred:", callback_occurred)
        finally:
            natlink.natDisconnect()


#---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
