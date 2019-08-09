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
Classes for recording audio to recognise.
"""

import threading
import time

import pyaudio


class PyAudioRecorder(object):
    """
    Class for recording audio from a pyaudio input stream.

    This class records on another thread to minimise dropped frames.
    """

    def __init__(self, config, read_interval=0.05):
        self.config = config
        self.read_interval = read_interval
        self._recording = False
        self._thread = None
        self._buffers = []
        self._condition = threading.Condition()
        self._lock = threading.RLock()

    @property
    def recording(self):
        """
        Whether audio is currently being recorded.

        :rtype: bool
        """
        return self._recording

    def start(self):
        """
        Start recording audio in another thread until :meth:`stop` is
        called.

        Audio buffers can be accessed with :meth:`get_buffers`.
        """
        if not self._thread:
            self._recording = True
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
            self._buffers = []

    def stop(self):
        """
        Stop recording audio.
        """
        self._recording = False
        if self._thread:
            self._thread.join(5)
            if not self._thread.is_alive():
                self._thread = None

    def _record(self):
        # Start recording audio on the current thread until stop() is
        # called.
        p = pyaudio.PyAudio()
        channels, rate = self.config.CHANNELS, self.config.RATE
        frames_per_buffer = self.config.FRAMES_PER_BUFFER
        pa_format = pyaudio.get_format_from_width(self.config.SAMPLE_WIDTH)
        stream = p.open(input=True, format=pa_format, channels=channels,
                        rate=rate, frames_per_buffer=frames_per_buffer)

        # Start recognising in a loop
        stream.start_stream()
        while self._recording:
            with self._condition:
                self._buffers.append(stream.read(frames_per_buffer))

                # Notify waiting threads (if any).
                self._condition.notifyAll()

            # This improves the performance; we don't need to process as
            # much audio as the device can read.
            time.sleep(self.read_interval)

        stream.close()
        p.terminate()
