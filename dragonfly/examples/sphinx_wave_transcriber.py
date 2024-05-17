#
# This file is part of Dragonfly.
# (c) Copyright 2019 by Dane Finlay
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
Example program for recognizing speech from a wave file using the CMU Pocket
Sphinx Dragonfly engine.

"""

import argparse
import contextlib
import logging
import os
import wave

from dragonfly import (Grammar, Rule, Dictation, RecognitionObserver,
                       get_engine)


#--------------------------------------------------------------------------
# Define the utilities necessary for recognizing speech from a wave file.

def process_wave_file(engine, path):
    """
    Use CMU Pocket Sphinx to recognize speech from a wave file and return
    the recognition results.

    This function checks that the wave file is valid. It raises an error
    if the file doesn't exist, if it can't be read or if the relevant
    WAV header parameters do not match those in the engine configuration.

    The wave file must use the same sample width, sample rate and number
    of channels that the acoustic model uses.

    If the file is valid, :meth:`engine.process_buffer` is then used to
    process the audio.

    Multiple utterances are supported.

    :param engine: sphinx engine instance
    :param path: wave file path
    :raises: IOError | OSError | ValueError
    :returns: recognition results
    :rtype: generator
    """
    # Check that path is a valid file.
    if not os.path.isfile(path):
        raise IOError("%r is not a file. Please use a different file"
                      " path." % (path,))

    # Get required audio configuration from the engine config.
    channels, sample_width, rate, chunk = (
        engine.config.CHANNELS,
        engine.config.SAMPLE_WIDTH,
        engine.config.RATE,
        engine.config.BUFFER_SIZE
    )

    # Open the wave file. Use contextlib to make sure that the file is
    # closed whether errors are raised or not.
    # Also register a custom recognition observer for the duration.
    obs = WaveRecognitionObserver(engine)
    with contextlib.closing(wave.open(path, "rb")) as wf, obs as obs:
        # Validate the wave file's header.
        if wf.getnchannels() != channels:
            message = ("WAV file '%s' should use %d channel(s), not %d!"
                       % (path, channels, wf.getnchannels()))
        elif wf.getsampwidth() != sample_width:
            message = ("WAV file '%s' should use sample width %d, not "
                       "%d!" % (path, sample_width, wf.getsampwidth()))
        elif wf.getframerate() != rate:
            message = ("WAV file '%s' should use sample rate %d, not "
                       "%d!" % (path, rate, wf.getframerate()))
        else:
            message = None

        if message:
            raise ValueError(message)

        # Process each audio buffer.
        for x in range(0, int(wf.getnframes() / chunk) + 1):
            data = wf.readframes(chunk)
            if not data:
                break

            engine.process_buffer(data)

            # Get the results from the observer.
            if obs.words:
                yield obs.words
                obs.words = ""

    # Log a warning if speech start or end weren't detected.
    if not obs.complete:
        logger = logging.getLogger("transcriber")
        logger.warning("Speech start/end wasn't detected in the wave"
                       " file!  Try adjusting -vad_* decoder params.")


class WaveRecognitionObserver(RecognitionObserver):
    def __init__(self, engine):
        RecognitionObserver.__init__(self)
        self.words = ""
        self.complete = None
        self.engine = engine

    def on_start(self):
        self.complete = False

    def on_recognition(self, words, results):
        self.complete = True
        self.words = " ".join(words)

    def on_failure(self, results):
        self.complete = True
        self.words = ""

    def __enter__(self):
        self.register()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unregister()


#--------------------------------------------------------------------------

def main():
    desc = "Program for transcribing speech from a wave file using the " \
           "CMU Pocket Sphinx Dragonfly engine."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("file", type=argparse.FileType("r"),
                        help="A .wav file containing speech.")
    args = parser.parse_args()
    file_path = args.file.name
    args.file.close()

    # Initialize the engine.
    engine = get_engine("sphinx")

    # Voice activity detection config values may need to be adjusted to
    # recognize speech.  Do this by changing the decoder's configuration
    # options.  The commented options below are the defaults.
    #decoder_config = engine.config.DECODER_CONFIG
    #decoder_config.set_int("-vad_startspeech", 10)  # Number of speech frames to trigger vad from silence to speech.
    #decoder_config.set_int("-vad_prespeech", 20)  # Number of speech frames to keep before silence to speech.
    #decoder_config.set_int("-vad_postspeech", 30)  # Number of silence frames to keep after from speech to silence.
    #decoder_config.set_float("-vad_threshold", 3.0)  # Threshold for decision between noise and silence frames. Log-ratio between signal level and noise level.

    # Connect the engine, now that configuration is complete.
    engine.connect()

    # Define and load a simple dictation-only grammar.  This will cause the
    # engine to recognize words from the default language model.
    grammar = Grammar("Transcriber grammar")
    grammar.add_rule(Rule("dictation", element=Dictation("text")))
    grammar.load()

    # Transcribe speech from the specified wave file.
    n = 0
    for result in process_wave_file(engine, file_path):
        print(result)
        if result: n += 1

    # Exit with 1 if there were no results.
    if n == 0:
        exit(1)


if __name__ == "__main__":
    main()
