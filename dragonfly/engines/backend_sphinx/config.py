# This Python file uses the following encoding: utf-8

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

# Configuration for wake/sleep phrases
# Note that the following CMU Sphinx tutorial has some advice on keyword thresholds
# values: https://cmusphinx.github.io/wiki/tutoriallm/#keyword-lists
START_ASLEEP = True
WAKE_PHRASE = "wake up"
WAKE_PHRASE_THRESHOLD = 1e-20
SLEEP_PHRASE = "go to sleep"
SLEEP_PHRASE_THRESHOLD = 1e-40

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
#
# If speech matched any normal rule that doesn't need to be spoken in sequence, it
# will be processed after the timeout period if it happens. Take the following rule
# specs for example:
# "hello"
# "hello <dictation>"
# If you say "hello" and don't start speaking the <dictation> part of the second
# rule, then the first "hello" rule will be processed instead.
NEXT_PART_TIMEOUT = 2.0
