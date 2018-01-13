"""
Default CMU Pocket Sphinx engine class configuration module
"""

from sphinxwrapper import DefaultConfig
from pyaudio import paInt16
import os

# Configuration for the Pocket Sphinx decoder.
DECODER_CONFIG = DefaultConfig()
# Silence the decoder output by default.
DECODER_CONFIG.set_string("-logfn", os.devnull)

# Keyword arguments given to the PyAudio.open method for opening a stream from a
# microphone. PyAudio streams are used by the engine to recognise speech from audio.
# You may wish to change the values to be optimal for the models you are using;
# Sphinx models require quite specific audio input to recognise speech correctly.
# The values below should work for the default US English models.
PYAUDIO_STREAM_KEYWORD_ARGS = {
    "input": True,              # stream is an input stream
    "format": paInt16,          # 16-bit rate
    "channels": 1,              # one channel (mono)
    "rate": 16000,              # 16kHz sample rate
    "frames_per_buffer": 2048,  # frames per buffer set to 2048
}

# User language for the engine to use.
LANGUAGE = "en"

# Timeout in seconds for speaking the next part of a rule involving dictation.
# This does not include the first part of such a rule. If this value is set to 0,
# then there will be no timeout.
NEXT_PART_TIMEOUT = 2.0
