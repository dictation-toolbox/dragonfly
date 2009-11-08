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
Tools for testing element classes
============================================================================

"""

from dragonfly              import *
from ..test                 import TestError, RecognitionFailure
from ..test.infrastructure  import Unique


#===========================================================================

class ElementTester(Grammar):

    _NotSet = Unique("NoRecognition")

    class _ElementTestRule(Rule):
        exported = True
        def process_recognition(self, node):
            self.grammar._process_recognition(node)

    #-----------------------------------------------------------------------

    def __init__(self, element, engine=None):
        Grammar.__init__(self, self.__class__.__name__, engine=engine)
        rule = self._ElementTestRule("rule", element)
        self.add_rule(rule)

    def recognize(self, words):
        if isinstance(words, basestring):
            words = words.split()

        if not self.loaded:
            self.load()
            unload_after_recognition = True
        else:
            unload_after_recognition = False

        self._recognized_value = self._NotSet
        try:
            # Make this grammar exclusive; this *probably* avoids other
            #  grammars from being active and receiving the mimicked
            #  recognition.
            self.set_exclusiveness(True)

            # Mimic recognition.
            try:
                mimic_method = self._mimic_methods[self.engine.name]
                mimic_method(self, words)
            except MimicFailure, e:
#                self._log.exception("Exception within mimic: %s" % (e,))
                self._recognized_value = RecognitionFailure
            except Exception, e:
                self._log.exception("Exception within recognition: %s" % (e,))
                raise

        except Exception, e:
            self._log.exception("Exception during recognition: %s" % (e,))
            raise
        finally:
            if unload_after_recognition:
                try:
                    self.unload()
                except Exception, e:
                    raise TestError("Failed to unload grammar: %s" % e)

        # If recognition was successful but this grammar did not
        #  receive the recognition callback, then apparently some other
        #  grammar hijacked it; raise a TestError to signal this
        #  undesired situation.
        if self._recognized_value == self._NotSet:
            self._log.error("Recognition hijacked. (Words: %s)" % (words,))
            raise TestError("Recognition hijacked. (Words: %s)" % (words,))

        # Return the value of the element after recognition.
        return self._recognized_value

    def _process_recognition(self, node):
        element_node = node.children[0]
        self._recognized_value = element_node.value()

    #-----------------------------------------------------------------------
    # Engine-specific logic.

    _mimic_methods = {}

    def _mimic_natlink(self, words):
        self.engine.mimic(words)
    _mimic_methods["natlink"] = _mimic_natlink

    def _mimic_sapi5(self, words):
        import time
        import win32con
        from ctypes import (windll, pointer, WinError, Structure,
                            c_int, c_uint, c_long)

        class POINT(Structure):
            _fields_ = [('x', c_long),
                        ('y', c_long)]

        class MSG(Structure):
            _fields_ = [('hwnd', c_int),
                        ('message', c_uint),
                        ('wParam', c_int),
                        ('lParam', c_int),
                        ('time', c_int),
                        ('pt', POINT)]

        class Obs(RecognitionObserver):
            status = "none"
            def on_recognition(self, words):
                self.status = "recognition: %r" % (words,)
            def on_failure(self):
                self.status = "failure"
        observer = Obs()
        observer.register()

        self.engine.mimic(words)

        timeout =  3
        NULL = c_int(win32con.NULL)
        if timeout != None:
            begin_time = time.time()
            timed_out = False
            windll.user32.SetTimer(NULL, NULL, int(timeout * 1000), NULL)
    
        message = MSG()
        message_pointer = pointer(message)

        while (not timeout) or (time.time() - begin_time < timeout):
            if windll.user32.GetMessageW(message_pointer, NULL, 0, 0) == 0:
                msg = str(WinError())
                self._log.error("GetMessageW() failed: %s" % msg)
                raise EngineError("GetMessageW() failed: %s" % msg)

            if message.message == win32con.WM_TIMER:
                # A timer message means this loop has timed out.
                timed_out = True
                break
            else:
                # Process other messages as normal.
                windll.user32.TranslateMessage(message_pointer)
                windll.user32.DispatchMessageW(message_pointer)

            if self._recognized_value != self._NotSet:
                # The previous message was a recognition which matched.
                break

        observer.unregister()
        if observer.status == "failure":
            raise MimicFailure("Mimic failed.")
#        elif observer.status == "none":
#            raise MimicFailure("Mimic failed, nothing happened.")

    _mimic_methods["sapi5"] = _mimic_sapi5
