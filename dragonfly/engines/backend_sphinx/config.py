#
# This file is part of Dragonfly.
# (c) Copyright 2019-2022 by Dane Finlay
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
Configuration classes and functions used by the engine.
"""

import os

from sphinxwrapper import DefaultConfig


def get_decoder_config_object():
    """ Get the default Sphinx decoder object for the engine. """
    decoder_config = DefaultConfig()

    # Silence the decoder output by default.
    decoder_config.set_string("-logfn", os.devnull)

    # Set voice activity detection configuration options for the decoder.
    # These values can be changed if noise in the background triggers speech
    # start and/or false recognitions (e.g. of short words) frequently.
    # Descriptions for VAD config options were retrieved from:
    # https://cmusphinx.github.io/doc/sphinxbase/fe_8h_source.html

    # Number of speech frames to trigger vad from silence to speech.
    decoder_config.set_int("-vad_startspeech", 10)

    # Number of speech frames to keep before silence to speech.
    decoder_config.set_int("-vad_prespeech", 20)

    # Number of silence frames to keep after from speech to silence.
    decoder_config.set_int("-vad_postspeech", 30)

    # Threshold for decision between noise and silence frames. Log-ratio
    # between signal level and noise level.
    decoder_config.set_float("-vad_threshold", 3.0)
    return decoder_config


class EngineConfig(object):
    """ Default engine configuration. """

    # Configuration for the Pocket Sphinx decoder.
    DECODER_CONFIG = get_decoder_config_object()

    # User language for the engine to use.
    LANGUAGE = "en"

    # Audio input configuration.
    # These values should match the requirements for the acoustic model
    # being used. Default values match the 16 kHz CMU US English models.
    CHANNELS = 1              # one channel (mono)
    SAMPLE_WIDTH = 2          # Sample width of 2 bytes/16 bits
    FORMAT = 'int16'
    RATE = 16000              # 16kHz sample rate
    BUFFER_SIZE = 1024        # Audio buffer size
