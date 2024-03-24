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
Example script for recognizing speech from a wave file using the CMU Pocket
Sphinx dragonfly engine.

"""

import argparse

from dragonfly import get_engine


def main():
    desc = "Example script for using the " \
        "'SphinxEngine.process_wave_file' method"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("file", type=argparse.FileType("r"),
                        help="A .wav file.")
    args = parser.parse_args()
    file_path = args.file.name
    args.file.close()

    # Set up the engine.
    engine = get_engine("sphinx")

    # Voice activity detection config values may need to be adjusted to
    # recognize speech.  Do this by changing the decoder's config.
    # Note that these values represent a number of audio frames, not time
    # intervals.
    # For example:
    engine.config.DECODER_CONFIG.set_int("-vad_postspeech", 30)

    # Process the wave file and print any results.
    # Note: process_wave_file() is a generator function.
    engine.connect()
    had_result = False
    for result in engine.process_wave_file(file_path):
        print(result)
        had_result = True

    # Exit with 1 if there were no results.
    if not had_result:
        exit(1)


if __name__ == "__main__":
    main()
