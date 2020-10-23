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
import collections, contextlib, datetime, itertools, logging, os, time, threading, wave
from io import open

from six import PY2, binary_type, text_type, print_
from six.moves import queue, range
import sounddevice
import webrtcvad

from ..base import EngineError

_log = logging.getLogger("engine")


class MicAudio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = 'int16'
    SAMPLE_WIDTH = 2
    SAMPLE_RATE = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 100
    BLOCK_SIZE_SAMPLES = int(SAMPLE_RATE / float(BLOCKS_PER_SECOND))  # Block size in number of samples
    BLOCK_DURATION_MS = int(1000 * BLOCK_SIZE_SAMPLES // SAMPLE_RATE)  # Block duration in milliseconds

    def __init__(self, callback=None, buffer_s=0, flush_queue=True, start=True, input_device=None, self_threaded=None, reconnect_callback=None):
        self.callback = callback if callback is not None else lambda in_data: self.buffer_queue.put(in_data, block=False)
        self.flush_queue = bool(flush_queue)
        self.input_device = input_device
        self.self_threaded = bool(self_threaded)
        if reconnect_callback is not None and not callable(reconnect_callback):
            _log.error("Invalid reconnect_callback not callable: %r", reconnect_callback)
            reconnect_callback = None
        self.reconnect_callback = reconnect_callback

        self.buffer_queue = queue.Queue(maxsize=(buffer_s * 1000 // self.BLOCK_DURATION_MS))
        self.stream = None
        self.thread = None
        self.thread_cancelled = False
        self.device_info = None

        try:
            device_list = sounddevice.query_devices(device=self.input_device)
            if not device_list:
                raise EngineError("No audio devices found.")
        except ValueError as e:
            message = e.args[0]
            message += "\nAvailable devices are:\n" + str(sounddevice.query_devices())
            raise ValueError(message)

        self._connect(start=start)

    def _connect(self, start=None):
        callback = self.callback
        def proxy_callback(in_data, frame_count, time_info, status):
            callback(bytes(in_data))  # Must copy data from temporary C buffer!

        self.stream = sounddevice.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.FORMAT,
            blocksize=self.BLOCK_SIZE_SAMPLES,
            # latency=80,
            device=self.input_device,
            callback=proxy_callback if not self.self_threaded else None,
        )

        if self.self_threaded:
            self.thread_cancelled = False
            self.thread = threading.Thread(target=self._reader_thread, args=(callback,))
            self.thread.daemon = True
            self.thread.start()

        if start:
            self.start()

        device_info = sounddevice.query_devices(self.stream.device)
        hostapi_info = sounddevice.query_hostapis(device_info['hostapi'])
        _log.info("streaming audio from '%s' using %s: %i sample_rate, %i block_duration_ms, %i latency_ms",
            device_info['name'], hostapi_info['name'], self.stream.samplerate, self.BLOCK_DURATION_MS, int(self.stream.latency*1000))
        self.device_info = device_info

    def _reader_thread(self, callback):
        while not self.thread_cancelled and self.stream and not self.stream.closed:
            if self.stream.active and self.stream.read_available >= self.stream.blocksize:
                in_data, overflowed = self.stream.read(self.stream.blocksize)
                # print('_reader_thread', read_available, len(in_data), overflowed, self.stream.blocksize)
                if overflowed:
                    _log.warning("audio stream overflow")
                callback(bytes(in_data))  # Must copy data from temporary C buffer!
            else:
                time.sleep(0.001)
                
    def _cancel_reader_thread(self):
        self.thread_cancelled = True
        if self.thread:
            self.thread.join()
            self.thread = None

    def destroy(self):
        self._cancel_reader_thread()
        if self.stream:
            self.stream.close()
            self.stream = None

    def reconnect(self):
        # FIXME: flapping
        old_device_info = self.device_info
        self._cancel_reader_thread()
        self.stream.close()
        self._connect(start=True)
        if self.reconnect_callback is not None:
            self.reconnect_callback(self)
        if self.device_info != old_device_info:
            raise EngineError("Audio reconnect could not reconnect to the same device")

    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.stop()

    def read(self, nowait=False):
        """Return a block of audio data. If nowait==False, waits for a block if necessary; else, returns False immediately if no block is available."""
        if self.stream or (self.flush_queue and not self.buffer_queue.empty()):
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
        assert self.FORMAT == 'int16'
        length_samples = length_bytes / self.SAMPLE_WIDTH
        return (float(length_samples) / self.SAMPLE_RATE)

    def write_wav(self, filename, data):
        # _log.debug("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == 'int16'
        wf.setsampwidth(self.SAMPLE_WIDTH)
        wf.setframerate(self.SAMPLE_RATE)
        wf.writeframes(data)
        wf.close()

    @staticmethod
    def print_list():
        print_("")
        print_("LISTING ALL INPUT DEVICES SUPPORTED BY PORTAUDIO")
        print_("(any device numbers not shown are for output only)")
        print_("")
        devices = sounddevice.query_devices()
        print_(devices)

        # for i in range(0, pa.get_device_count()):
        #     info = pa.get_device_info_by_index(i)

        #     if info['maxInputChannels'] > 0:  # microphone? or just speakers
        #         print_("DEVICE #%d" % info['index'])
        #         print_("    %s" % info['name'])
        #         print_("    input channels = %d, output channels = %d, defaultSampleRate = %d" %
        #             (info['maxInputChannels'], info['maxOutputChannels'], info['defaultSampleRate']))
        #         # print_(info)
        #         try:
        #           supports16k = pa.is_format_supported(16000,  # sample rate
        #               input_device = info['index'],
        #               input_channels = info['maxInputChannels'],
        #               input_format = pyaudio.paInt16)
        #         except ValueError:
        #           print_("    NOTE: 16k sampling not supported, configure pulseaudio to use this device")

        print_("")


class VADAudio(MicAudio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, aggressiveness=3, **kwargs):
        super(VADAudio, self).__init__(**kwargs)
        self.vad = webrtcvad.Vad(aggressiveness)

    def vad_collector(self, start_window_ms=150, start_padding_ms=100,
        end_window_ms=150, end_padding_ms=None, complex_end_window_ms=None,
        ratio=0.8, blocks=None, nowait=False, audio_auto_reconnect=False,
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
                if audio_auto_reconnect and (num_empty_blocks >= audio_reconnect_threshold_blocks) and (time.time() - last_good_block_time >= audio_reconnect_threshold_time):
                    _log.warning("%s: no good block received recently, so reconnecting audio", self)
                    self.reconnect()
                    num_empty_blocks = 0
                    last_good_block_time = time.time()
                in_complex_phrase = yield False

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

        if triggered:
            # We were in a phrase, so we must terminate it (this may be abrupt!)
            yield None

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
    Also, optionally stores the last `maxlen` recognitions as `AudioStoreEntry` objects,
    indexed in reverse order (0 is most recent), and advanced upon calling `finalize()`.
    Note: `finalize()` should be called after the recognition has been parsed and its actions executed.

    Constructor arguments:
    - *maxlen* (*int*, default *None*): if set, the number of previous recognitions to temporarily store.
    - *save_dir* (*str*, default *None*): if set, the directory to save the `retain.tsv` file and optionally wav files.
    - *save_metadata* (*bool*, default *None*): whether to automatically save the recognition metadata.
    - *save_audio* (*bool*, default *None*): whether to automatically save the recognition audio data (in addition to just the recognition metadata).
    - *retain_approval_func* (*Callable*, default *None*): if set, will be called with the `AudioStoreEntry` object about to be saved,
        and should return `bool` whether to actually save. Example: `retain_approval_func=lambda entry: bool(entry.grammar_name != 'noisegrammar')`
    """

    def __init__(self, audio_obj, maxlen=None, save_dir=None, save_audio=None, save_metadata=None, retain_approval_func=None):
        self.audio_obj = audio_obj
        self.maxlen = maxlen
        self.save_dir = save_dir
        self.save_audio = save_audio
        self.save_metadata = save_metadata
        if self.save_dir:
            _log.info("retaining recognition audio and/or metadata to '%s'", self.save_dir)
        self.retain_approval_func = retain_approval_func
        self.deque = collections.deque(maxlen=maxlen) if maxlen else None
        self.blocks = []

    current_audio_data = property(lambda self: b''.join(bytes(self.blocks)) if PY2 else b''.join(self.blocks))
    current_audio_length_ms = property(lambda self: len(self.blocks) * self.audio_obj.BLOCK_DURATION_MS)

    def add_block(self, block):
        self.blocks.append(block)

    def finalize(self, text, grammar_name, rule_name, likelihood=None, tag='', has_dictation=None):
        """ Finalizes current utterance, creating its AudioStoreEntry and saving it (if enabled). """
        entry = AudioStoreEntry(self.current_audio_data, grammar_name, rule_name, text, likelihood, tag, has_dictation)
        if self.deque is not None:
            if len(self.deque) == self.deque.maxlen:
                self.save(-1)  # Save oldest, which is about to be evicted
            self.deque.appendleft(entry)
        self.blocks = []

    def cancel(self):
        self.blocks = []

    def save(self, index):
        """ Saves AudioStoreEntry for given index (0 is most recent). """
        if slice(index).indices(len(self.deque))[1] >= len(self.deque):
            raise EngineError("Invalid index to save in AudioStore")
        if not self.save_dir:
            return
        if not os.path.isdir(self.save_dir):
            _log.warning("Recognition data was not retained because '%s' was not a directory" % self.save_dir)
            return

        entry = self.deque[index]
        if (not self.save_audio) and (not self.save_metadata) and (not entry.force_save):
            return
        if self.retain_approval_func and not self.retain_approval_func(entry):
            return
        if self.save_audio or entry.force_save:
            filename = os.path.join(self.save_dir, "retain_%s.wav" % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f"))
            self.audio_obj.write_wav(filename, entry.audio_data)
        else:
            filename = ''

        with open(os.path.join(self.save_dir, "retain.tsv"), 'a', encoding='utf-8') as tsv_file:
            tsv_file.write(u'\t'.join([
                    filename,
                    text_type(self.audio_obj.get_wav_length_s(entry.audio_data)),
                    entry.grammar_name,
                    entry.rule_name,
                    entry.text,
                    text_type(entry.likelihood),
                    text_type(entry.tag),
                    text_type(entry.has_dictation),
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
    __nonzero__ = __bool__  # PY2 compatibility

class AudioStoreEntry(object):
    __slots__ = ('audio_data', 'grammar_name', 'rule_name', 'text', 'likelihood', 'tag', 'has_dictation', 'force_save')

    def __init__(self, audio_data, grammar_name, rule_name, text, likelihood, tag, has_dictation, force_save=False):
        self.audio_data = audio_data
        self.grammar_name = grammar_name
        self.rule_name = rule_name
        self.text = text
        self.likelihood = likelihood
        self.tag = tag
        self.has_dictation = has_dictation
        self.force_save = force_save

    def set(self, key, value):
        """ Sets given key (as *str*) to value, returning the AudioStoreEntry for chaining; usable in lambda functions. """
        setattr(self, key, value)
        return self


class WavAudio(object):
    """ Class for mimicking normal microphone input, but from wav files. """

    @classmethod
    def read_file(cls, filename, realtime=False):
        """ Yields raw audio blocks from wav file, terminated by a None element. """
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

            next_time = time.time()
            for _ in range(0, int(file.getnframes() / MicAudio.BLOCK_SIZE_SAMPLES) + 1):
                data = file.readframes(MicAudio.BLOCK_SIZE_SAMPLES)
                if not data:
                    break
                if realtime:
                    time_behind = next_time - time.time()
                    if time_behind > 0:
                        time.sleep(time_behind)
                    next_time += float(MicAudio.BLOCK_SIZE_SAMPLES) / MicAudio.SAMPLE_RATE
                yield data
            yield None

    @classmethod
    def read_file_with_vad(cls, filename, realtime=False, **kwargs):
        """ Yields raw audio blocks from wav file, after processing by VAD, terminated by a None element. """
        vad_audio = VADAudio()
        vad_audio_iter = vad_audio.vad_collector(blocks=cls.read_file(filename, realtime=realtime), **kwargs)
        return vad_audio_iter
