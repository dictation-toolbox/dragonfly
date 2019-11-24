#
# This file is part of Dragonfly.
# (c) Copyright 2019 by David Zurow
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
Audio input/output classes for Kaldi backend
"""

from __future__ import division, print_function
import collections, contextlib, datetime, itertools, logging, os, time, wave
from io import open

from six import binary_type, text_type, print_
from six.moves import queue, range
import pyaudio
import webrtcvad

from ..base import EngineError

_log = logging.getLogger("engine")


class MicAudio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    SAMPLE_WIDTH = 2
    SAMPLE_RATE = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50
    BLOCK_SIZE_SAMPLES = int(SAMPLE_RATE / float(BLOCKS_PER_SECOND))  # Block size in number of samples
    BLOCK_DURATION_MS = int(1000 * BLOCK_SIZE_SAMPLES // SAMPLE_RATE)  # Block duration in milliseconds

    def __init__(self, callback=None, buffer_s=0, flush_queue=True, start=True, input_device_index=None):
        self.callback = callback if callback is not None else lambda in_data: self.buffer_queue.put(in_data, block=False)
        self.flush_queue = flush_queue
        self.input_device_index = input_device_index

        self.buffer_queue = queue.Queue(maxsize=(buffer_s * 1000 // self.BLOCK_DURATION_MS))
        self.pa = pyaudio.PyAudio()
        self._connect(start=start)

    def _connect(self, start=None):
        callback = self.callback
        def proxy_callback(in_data, frame_count, time_info, status):
            callback(in_data)
            return (None, pyaudio.paContinue)
        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.BLOCK_SIZE_SAMPLES,
            stream_callback=proxy_callback,
            input_device_index=self.input_device_index,
            start=bool(start),
        )
        self.active = True
        info = self.pa.get_default_input_device_info() if self.input_device_index is None else self.pa.get_device_info_by_index(self.input_device_index)
        _log.info("streaming audio from '%s': %i sample_rate, %i block_duration_ms", info['name'], self.SAMPLE_RATE, self.BLOCK_DURATION_MS)

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.active = False

    def reconnect(self):
        self.stream.stop_stream()
        self.stream.close()
        self._connect(start=True)

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()

    def read(self, nowait=False):
        """Return a block of audio data. If nowait==False, waits for a block if necessary; else, returns False immediately if no block is available."""
        if self.active or (self.flush_queue and not self.buffer_queue.empty()):
            if nowait:
                try:
                    return self.buffer_queue.get_nowait()  # Return good block if available
                except queue.Empty as e:
                    return False  # Queue is empty for now
            else:
                return self.buffer_queue.get()  # Wait for a good block and return it
        else:
            return None  # We are done

    def read_loop(self, callback):
        """Block looping reading, repeatedly passing a block of audio data to callback."""
        for block in iter(self):
            callback(block)

    def iter(self, nowait=False):
        """Generator that yields all audio blocks from microphone."""
        while True:
            block = self.read(nowait=nowait)
            if block is None:
                break
            yield block

    def __iter__(self):
        """Generator that yields all audio blocks from microphone."""
        return self.iter()

    def get_wav_length_s(self, data):
        assert isinstance(data, binary_type)
        length_bytes = len(data)
        assert self.FORMAT == pyaudio.paInt16
        length_samples = length_bytes / self.SAMPLE_WIDTH
        return (float(length_samples) / self.SAMPLE_RATE)

    def write_wav(self, filename, data):
        # _log.debug("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(self.SAMPLE_WIDTH)
        wf.setframerate(self.SAMPLE_RATE)
        wf.writeframes(data)
        wf.close()

    @staticmethod
    def print_list():
        pa = pyaudio.PyAudio()

        print_("")
        print_("LISTING ALL INPUT DEVICES SUPPORTED BY PORTAUDIO")
        print_("(any device numbers not shown are for output only)")
        print_("")

        for i in range(0, pa.get_device_count()):
            info = pa.get_device_info_by_index(i)

            if info['maxInputChannels'] > 0:  # microphone? or just speakers
                print_("DEVICE #%d" % info['index'])
                print_("    %s" % info['name'])
                print_("    input channels = %d, output channels = %d, defaultSampleRate = %d" %
                    (info['maxInputChannels'], info['maxOutputChannels'], info['defaultSampleRate']))
                # print_(info)
                try:
                  supports16k = pa.is_format_supported(16000,  # sample rate
                      input_device = info['index'],
                      input_channels = info['maxInputChannels'],
                      input_format = pyaudio.paInt16)
                except ValueError:
                  print_("    NOTE: 16k sampling not supported, configure pulseaudio to use this device")

        print_("")


class VADAudio(MicAudio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, aggressiveness=3, **kwargs):
        super(VADAudio, self).__init__(**kwargs)
        self.vad = webrtcvad.Vad(aggressiveness)

    def vad_collector(self, start_window_ms=150, start_padding_ms=100,
        end_window_ms=150, end_padding_ms=None, complex_end_window_ms=None,
        ratio=0.8, blocks=None, nowait=False,
        ):
        """Generator/coroutine that yields series of consecutive audio blocks comprising each phrase, separated by yielding a single None.
            Determines voice activity by ratio of blocks in window_ms. Uses a buffer to include window_ms prior to being triggered.
            Example: (block, ..., block, None, block, ..., block, None, ...)
                      |----phrase-----|        |----phrase-----|
        """
        assert end_padding_ms == None, "end_padding_ms not supported yet"
        num_start_window_blocks = max(1, int(start_window_ms // self.BLOCK_DURATION_MS))
        num_start_padding_blocks = max(0, int((start_padding_ms or 0) // self.BLOCK_DURATION_MS))
        num_end_window_blocks = max(1, int(end_window_ms // self.BLOCK_DURATION_MS))
        num_complex_end_window_blocks = max(1, int((complex_end_window_ms or end_window_ms) // self.BLOCK_DURATION_MS))
        num_end_padding_blocks = max(0, int((end_padding_ms or 0) // self.BLOCK_DURATION_MS))
        _log.debug("%s: vad_collector: num_start_window_blocks=%s num_end_window_blocks=%s num_complex_end_window_blocks=%s",
            self, num_start_window_blocks, num_end_window_blocks, num_complex_end_window_blocks)
        audio_reconnect_threshold_blocks = 5
        audio_reconnect_threshold_time = 50 * self.BLOCK_DURATION_MS / 1000

        ring_buffer = collections.deque(maxlen=max(
            (num_start_window_blocks + num_start_padding_blocks),
            (num_end_window_blocks + num_end_padding_blocks),
            (num_complex_end_window_blocks + num_end_padding_blocks),
        ))
        ring_buffer_recent_slice = lambda num_blocks: itertools.islice(ring_buffer, max(0, (len(ring_buffer) - num_blocks)), None)

        triggered = False
        in_complex_phrase = False
        num_empty_blocks = 0
        last_good_block_time = time.time()

        if blocks is None: blocks = self.iter(nowait=nowait)
        for block in blocks:
            if block is False or block is None:
                # Bad/empty block
                num_empty_blocks += 1
                if (num_empty_blocks >= audio_reconnect_threshold_blocks) and (time.time() - last_good_block_time >= audio_reconnect_threshold_time):
                    _log.warning("%s: no good block received recently, so reconnecting audio")
                    self.reconnect()
                    num_empty_blocks = 0
                    last_good_block_time = time.time()
                in_complex_phrase = yield block

            else:
                # Good block
                num_empty_blocks = 0
                last_good_block_time = time.time()
                is_speech = self.vad.is_speech(block, self.SAMPLE_RATE)

                if not triggered:
                    # Between phrases
                    ring_buffer.append((block, is_speech))
                    num_voiced = len([1 for (_, speech) in ring_buffer_recent_slice(num_start_window_blocks) if speech])
                    if num_voiced >= (num_start_window_blocks * ratio):
                        # Start of phrase
                        triggered = True
                        for block, _ in ring_buffer_recent_slice(num_start_padding_blocks + num_start_window_blocks):
                            # print('|' if is_speech else '.', end='')
                            # print('|' if in_complex_phrase else '.', end='')
                            in_complex_phrase = yield block
                        # print('#', end='')
                        ring_buffer.clear()

                else:
                    # Ongoing phrase
                    in_complex_phrase = yield block
                    # print('|' if is_speech else '.', end='')
                    # print('|' if in_complex_phrase else '.', end='')
                    ring_buffer.append((block, is_speech))
                    num_unvoiced = len([1 for (_, speech) in ring_buffer_recent_slice(num_end_window_blocks) if not speech])
                    num_complex_unvoiced = len([1 for (_, speech) in ring_buffer_recent_slice(num_complex_end_window_blocks) if not speech])
                    if (not in_complex_phrase and num_unvoiced >= (num_end_window_blocks * ratio)) or \
                        (in_complex_phrase and num_complex_unvoiced >= (num_complex_end_window_blocks * ratio)):
                        # End of phrase
                        triggered = False
                        in_complex_phrase = yield None
                        # print('*')
                        ring_buffer.clear()

    def debug_print_simple(self):
        print("block_duration_ms=%s" % self.BLOCK_DURATION_MS)
        for block in self.iter(nowait=False):
            is_speech = self.vad.is_speech(block, self.SAMPLE_RATE)
            print('|' if is_speech else '.', end='')

    def debug_loop(self, *args, **kwargs):
        audio_iter = self.vad_collector(*args, **kwargs)
        next(audio_iter)
        while True:
            block = audio_iter.send(False)


class AudioStore(object):
    """
    Stores the current audio data being recognized, which is cleared upon calling `finalize()`.
    Also, optionally stores the last `maxlen` recognitions as lists [audio, text, grammar_name, rule_name, misrecognition],
    indexed in reverse order (0 is most recent), and advanced upon calling `finalize()`.
    Note: `finalize()` should be called after the recognition has been parsed and its actions executed.

    Constrictor arguments:
    - *save_audio* (bool, default *None*): whether to save the audio data (in addition to just the recognition metadata)
    """

    def __init__(self, audio_obj, maxlen=None, save_dir=None, save_audio=None, auto_save_predicate_func=None):
        self.audio_obj = audio_obj
        self.maxlen = maxlen
        self.save_dir = save_dir
        self.save_audio = save_audio
        if self.save_dir:
            if self.save_audio:
                _log.info("retaining audio and recognition metadata to '%s'", self.save_dir)
            else:
                _log.info("retaining recognition metadata to '%s'", self.save_dir)
        self.auto_save_predicate_func = auto_save_predicate_func
        self.deque = collections.deque(maxlen=maxlen) if maxlen else None
        self.blocks = []

    current_audio_data = property(lambda self: b''.join(self.blocks))
    current_audio_length_ms = property(lambda self: len(self.blocks) * self.audio_obj.BLOCK_DURATION_MS)

    def add_block(self, block):
        self.blocks.append(block)

    def finalize(self, text, grammar_name, rule_name, likelihood=None):
        entry = AudioStoreEntry(self.current_audio_data, grammar_name, rule_name, text, likelihood, False)
        if self.deque is not None:
            if len(self.deque) == self.deque.maxlen:
                self.save(-1)  # Save oldest, which is about to be evicted
            self.deque.appendleft(entry)
        # if self.auto_save_predicate_func and self.auto_save_predicate_func(*entry):
        #     self.save(0)
        self.blocks = []

    def save(self, index):
        if slice(index).indices(len(self.deque))[1] >= len(self.deque):
            raise EngineError("Invalid index to save in AudioStore")
        if not self.save_dir:
            return
        if not os.path.isdir(self.save_dir):
            _log.warning("Recognition data was not retained because '%s' was not a directory" % self.save_dir)
            return

        entry = self.deque[index]
        if self.save_audio:
            filename = os.path.join(self.save_dir, "retain_%s.wav" % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f"))
            self.audio_obj.write_wav(filename, entry.audio)
        else:
            filename = ''

        with open(os.path.join(self.save_dir, "retain.tsv"), 'a', encoding='utf-8') as tsv_file:
            tsv_file.write(u'\t'.join([
                    filename,
                    text_type(self.audio_obj.get_wav_length_s(entry.audio)),
                    entry.grammar_name,
                    entry.rule_name,
                    entry.text,
                    text_type(entry.likelihood),
                    text_type(entry.misrecognition),
                ]) + '\n')

    def save_all(self, remove=True):
        if self.deque:
            for i in reversed(range(len(self.deque))):
                self.save(i)
            if remove:
                self.deque.clear()

    def __getitem__(self, key):
        return self.deque[key]
    def __len__(self):
        return len(self.deque)
    def __bool__(self):
        return True
    def __nonzero__(self):
        return True

class AudioStoreEntry(object):
    __slots__ = ('audio', 'grammar_name', 'rule_name', 'text', 'likelihood', 'misrecognition')

    def __init__(self, audio, grammar_name, rule_name, text, likelihood, misrecognition):
        self.audio = audio
        self.grammar_name = grammar_name
        self.rule_name = rule_name
        self.text = text
        self.likelihood = likelihood
        self.misrecognition = misrecognition

    def set(self, key, value):
        setattr(self, key, value)


class WavAudio(object):

    @classmethod
    def read_file(cls, filename):
        """ Yields raw audio blocks from wav file. """
        if not os.path.isfile(filename):
            raise IOError("'%s' is not a file. Please use a different file path.")

        with contextlib.closing(wave.open(filename, 'rb')) as file:
            # Validate the wave file's header
            if file.getnchannels() != MicAudio.CHANNELS:
                raise ValueError("WAV file '%s' should use %d channel(s), not %d!"
                           % (filename, MicAudio.CHANNELS, file.getnchannels()))
            elif file.getsampwidth() != MicAudio.SAMPLE_WIDTH:
                raise ValueError("WAV file '%s' should use sample width %d, not "
                           "%d!" % (filename, MicAudio.SAMPLE_WIDTH, file.getsampwidth()))
            elif file.getframerate() != MicAudio.SAMPLE_RATE:
                raise ValueError("WAV file '%s' should use sample rate %d, not "
                           "%d!" % (filename, MicAudio.SAMPLE_RATE, file.getframerate()))

            for _ in range(0, int(file.getnframes() / MicAudio.BLOCK_SIZE_SAMPLES) + 1):
                data = file.readframes(MicAudio.BLOCK_SIZE_SAMPLES)
                if not data:
                    break
                yield data
            yield None
