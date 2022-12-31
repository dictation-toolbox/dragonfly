#
# This file is part of Dragonfly.
# (c) Copyright 2017-2022 by Dane Finlay
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
Classes for recording audio to recognise.
"""

import threading
import time

import sounddevice


class AudioRecorder(object):
    """
    Class for recording audio from an input stream.

    This class records on another thread to minimise dropped frames.
    """

    def __init__(self, config, read_interval=0.05):
        self.config = config
        self.read_interval = read_interval
        self._thread = None
        self._buffers = []
        self._condition = threading.Condition()
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

    @property
    def recording(self):
        """
        Whether audio is currently being recorded.

        :rtype: bool
        """
        return not self._stop_event.isSet()

    def start(self):
        """
        Start recording audio in another thread until :meth:`stop` is
        called.

        Audio buffers can be accessed with :meth:`get_buffers`.
        """
        if not self._thread:
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._record)
            self._thread.setDaemon(True)
            self._thread.start()

    def get_buffers(self, clear=True):
        """
        Return any stored audio data, optionally clearing the internal list.

        :param clear: whether to clear the internal buffer list.
        :type clear: bool
        :returns: audio buffer list
        :rtype: list
        """
        if self._thread:
            with self._condition:
                self._condition.wait()
                buffers = list(self._buffers)
                if clear:
                    self.clear_buffers()
                return buffers
        else:
            buffers = list(self._buffers)
            if clear:
                self.clear_buffers()
            return buffers

    def clear_buffers(self):
        """
        Clear the internal buffer list.
        """
        with self._lock:
            while len(self._buffers) > 0: self._buffers.pop(0)

    def stop(self):
        """
        Stop recording audio.
        """
        self._stop_event.set()

        # Try to make this call synchronous.
        if self._thread:
            self._thread.join(5)
            if not self._thread.is_alive():
                self._thread = None

    def _record(self):
        # Start recording audio on the current thread until stop() is
        # called.
        buffer_size = self.config.BUFFER_SIZE
        stream = sounddevice.RawInputStream(
            dtype=self.config.FORMAT,
            channels=self.config.CHANNELS,
            samplerate=self.config.RATE,
            blocksize=buffer_size // 2,
        )
        stream.start()
        try:
            while not self._stop_event.isSet():
                with self._condition:
                    data, _ = stream.read(buffer_size // 2)
                    self._buffers.append(data)

                    # Notify waiting threads (if any).
                    self._condition.notifyAll()

                # This improves the performance; we don't need to
                #  process as much audio as the device can read.
                time.sleep(self.read_interval)
        finally:
            stream.close()
