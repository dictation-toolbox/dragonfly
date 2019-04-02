"""
Example script for recognising speech from a wave file using the CMU Pocket
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
    # process_wave() handles START_ASLEEP = True (default), but a warning
    # message will be logged. We can suppress that here.
    engine = get_engine("sphinx")
    engine.config.START_ASLEEP = False

    # Voice activity detection config values may need to be adjusted to
    # recognise speech. Do this by changing the decoder's config.
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
