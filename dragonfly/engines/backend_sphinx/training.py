"""
Utilities for training CMU Pocket Sphinx acoustic models.
"""

import os

import wave
from six import string_types


class TrainingDataWriter(object):
    """
    Class to create .fileids, .transcriptions and .wav files in a specified
    directory.

    If the directory doesn't exist, this class will attempt to create it.
    """
    def __init__(self, data_dir, transcript_name, channels, sample_width, rate):
        """
        :param data_dir: directory where training files should be created.
        :param transcript_name: common file name to use for training files.
        :param channels: number of channels to specify in WAVE header.
        :param sample_width: sample width to specify in the WAVE header.
        :param rate: sample rate to specify in the WAVE header.
        :raises: IOError | OSError
        """
        # Check if data_dir exists and is a directory.
        exists = os.path.exists(data_dir)
        if exists and not os.path.isdir(data_dir):
            raise IOError("'%s' is not a directory. Please use a different file "
                          "file path.")

        # Attempt to make the directory if it doesn't exist. Let the caller handle
        # any errors.
        elif not exists:
            os.mkdir(data_dir)

        # Save parameters for later use.
        self._data_dir = data_dir
        self._transcript_name = transcript_name
        self._channels, self._sample_width = channels, sample_width
        self._rate = rate

        # Open the .fileids and .transcription files (they can exist already)
        fileids_path = os.path.join(data_dir, "%s.fileids" % transcript_name)
        transcriptions_path = os.path.join(data_dir, "%s.transcriptions"
                                           % transcript_name)
        self._fileids_file = open(fileids_path, "a")
        self._transcriptions_file = open(transcriptions_path, "a")

        # Store the next transcript id.
        self._transcript_id = self._get_next_transcript_id()

        # Open a new .wav file.
        self._wav_file = self._get_new_wav_file()

    def _get_next_transcript_id(self):
        """
        Generate a new transcript id based on the relevant .wav files in the data
        directory.
        :rtype: int
        """
        # Find all <transcript_name>.wav files and generate a list of IDs.
        transcript_ids = []
        for f in os.listdir(self._data_dir):
            if f.startswith(self._transcript_name) and f.endswith(".wav"):
                # Strip the transcript name from the start and '.wav' from the end
                # and cast the remaining id string into an integer if it is one.
                id_ = f[len(self._transcript_name):][0:-4]
                if id_.isdigit():
                    transcript_ids.append(int(id_))

        if transcript_ids:
            return max(transcript_ids) + 1
        else:
            return 1

    @property
    def current_wav_filename(self):
        """
        The current .wav filename.
        :rtype: str
        """
        return "%s%04d.wav" % (self._transcript_name, self._transcript_id)

    @property
    def current_absolute_wav_file_path(self):
        return os.path.join(self._data_dir, self.current_wav_filename)

    def _get_new_wav_file(self):
        # Open the .wav file using the lowest filename starting at
        # <transcript_name>0001.wav.
        # Get the next guaranteed transcript ID and absolute file path.
        self._transcript_id = self._get_next_transcript_id()
        wav_path = self.current_absolute_wav_file_path

        # Open a new wave file and write the header.
        # Based on this: https://people.csail.mit.edu/hubert/pyaudio/#record-example
        wf = wave.open(wav_path, "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._sample_width)
        wf.setframerate(self._rate)
        return wf

    def open_next_wav_file(self):
        """
        Open the next .wav file and write the header information.
        """
        self._wav_file = self._get_new_wav_file()

    def write_to_wave_file(self, buf):
        """
        Method to write an audio buffer to the current .wav file.
        :param buf:
        """
        self._wav_file.writeframes(buf)

    def _discard_current_data(self):
        """
        Internal method to discard the current .wav file.
        """
        self._wav_file.close()
        file_path = self.current_absolute_wav_file_path
        if os.path.exists(file_path):
            os.remove(file_path)

    def finalise(self, hypothesis):
        """
        Method to finish writing training data to audio and text files.
        If passed None or an empty string as a hypothesis, the recording
        will be discarded.
        :param hypothesis: str | None
        """
        if hypothesis is not None and not isinstance(hypothesis, string_types):
            raise TypeError("hypothesis must be a string or None.")

        if not hypothesis:
            self._discard_current_data()
        else:
            # Finish writing the .wav file.
            self._wav_file.close()

            # Get the current .wav filename without the '.wav'.
            transcript_identifier = self.current_wav_filename[0:-4]

            # Append some information to the .fileids and .transcriptions files.
            self._transcriptions_file.write(
                "<s> %s </s> (%s)\n" % (hypothesis, transcript_identifier)
            )
            self._fileids_file.write("%s\n" % transcript_identifier)

    def close_files(self):
        """
        Method to close any open files and discard the current .wav file.
        Should be used in engine.disconnect().
        """
        self._transcriptions_file.close()
        self._fileids_file.close()

        # Also close and discard the current .wav file
        self._discard_current_data()

    def __del__(self):
        # Close any open files if this writer goes out of scope or is deleted.
        self.close_files()
