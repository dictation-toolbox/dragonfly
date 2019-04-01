"""
Utilities for training CMU Pocket Sphinx acoustic models.
"""

import contextlib
import os
import time
import wave


def write_training_data(config, frames, hypothesis):
    """
    Write audio frames and the speech hypothesis to new files.

    Audio frames for null hypotheses will not be recorded.

    :raises: IOError | OSError
    """
    if not hypothesis:
        return

    # Check that the directory exists.
    data_dir = config.TRAINING_DATA_DIR
    if not os.path.isdir(data_dir):
        raise IOError("'%s' is not a directory" % data_dir)

    # Use the current time for the file IDs.
    now = time.time()
    base_filename = "%s-%.2f" % (config.TRANSCRIPT_NAME, now)
    wav_filename = base_filename + ".wav"
    txt_filename = base_filename + ".txt"

    # Open and write to a new wave file.
    # Based on the PyAudio record example:
    # https://people.csail.mit.edu/hubert/pyaudio/#record-example
    wav_path = os.path.join(data_dir, wav_filename)
    with contextlib.closing(wave.open(wav_path, "wb")) as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(config.SAMPLE_WIDTH)
        wf.setframerate(config.RATE)
        wf.writeframes(b''.join(frames))

    txt_path = os.path.join(data_dir, txt_filename)
    with open(txt_path, "w") as f:
        f.write(hypothesis)

def write_transcript_files(config, fileids_path, transcriptions_path):
    """
    Write .fileids and .transcriptions using the files in a directory.

    :raises: IOError | OSError
    """
    # Check that the directory exists.
    data_dir = config.TRAINING_DATA_DIR
    transcript_name = config.TRANSCRIPT_NAME
    if not os.path.isdir(data_dir):
        raise IOError("'%s' is not a directory" % data_dir)

    # Get the relevant files from a directory listing.
    def relevant_entry(x):
        return (
            # Must start with "training" by default and end with .wav.
            x.startswith(transcript_name) and x.endswith(".wav") and

            # There must be an accompanying .txt file.
            os.path.isfile(os.path.join(data_dir, "%s.txt" % x[:-4]))
        )

    base_filenames = [f[0:-4] for f in os.listdir(data_dir)
                       if relevant_entry(f)]

    # Sort by time in ascending order.
    base_filenames = sorted(base_filenames)

    # Process each relevant file, adding content to the transcript files
    # where necessary.
    path1, path2 = fileids_path, transcriptions_path
    with open(path1, "w") as f1, open(path2, "w") as f2:
        for name in base_filenames:
            # Get the hypothesis from the text file.
            txt_path = os.path.join(transcript_name, name + ".txt")
            with open(txt_path, "r") as txt_file:
                hypothesis = txt_file.readline().strip()

            # Skip entries with null hypotheses.
            if not hypothesis:
                continue

            # Write data to both files.
            f1.write("%s\n" % name)
            f2.write("<s> %s </s> (%s)\n" % (hypothesis, name))
