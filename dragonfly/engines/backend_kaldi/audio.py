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

import collections, wave, logging, os, datetime

from six import print_
from six.moves import queue
import pyaudio
import webrtcvad

_log = logging.getLogger("engine")


class MicAudio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    RATE = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    def __init__(self, callback=None, buffer_s=0, flush_queue=True, start=True, input_device_index=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            callback(in_data)
            return (None, pyaudio.paContinue)
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data, block=False)
        self.sample_rate = self.RATE
        self.flush_queue = flush_queue
        self.buffer_queue = queue.Queue(maxsize=(buffer_s * 1000 // self.block_duration_ms))
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.block_size,
            stream_callback=proxy_callback,
            input_device_index=input_device_index,
            start=bool(start),
        )
        self.active = True
        _log.info("%s: streaming audio from microphone: %i sample_rate, %i block_duration_ms", self, self.sample_rate, self.block_duration_ms)

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.active = False

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()

    def read(self, nowait=False):
        """Return a block of audio data. If nowait==False, waits for a block if necessary; else, returns False immediately if no block is available."""
        if self.active or (self.flush_queue and not self.buffer_queue.empty()):
            if nowait:
                try:
                    return self.buffer_queue.get_nowait()
                except queue.Empty as e:
                    return False
            else:
                return self.buffer_queue.get()
        else:
            return None

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

    block_size = property(lambda self: int(self.sample_rate / float(self.BLOCKS_PER_SECOND)))
    block_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def write_wav(self, filename, data):
        # _log.debug("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
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

    def vad_collector(self, padding_ms=300, ratio=0.75, blocks=None, nowait=False):
        """Generator that yields series of consecutive audio blocks comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of blocks in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (block, ..., block, None, block, ..., block, None, ...)
                      |---utterence---|        |---utterence---|
        """
        # FIXME: error reporting for invalid padding_ms
        if blocks is None: blocks = self.iter(nowait=nowait)
        num_padding_blocks = padding_ms // self.block_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_blocks)
        triggered = False

        for block in blocks:
            if block is False or block is None:
                yield block

            else:
                is_speech = self.vad.is_speech(block, self.sample_rate)

                if not triggered:
                    ring_buffer.append((block, is_speech))
                    num_voiced = len([f for f, speech in ring_buffer if speech])
                    if num_voiced > ratio * ring_buffer.maxlen:
                        # Start of phrase
                        triggered = True
                        for f, s in ring_buffer:
                            yield f
                        ring_buffer.clear()

                else:
                    # Ongoing phrase
                    yield block
                    ring_buffer.append((block, is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    if num_unvoiced > ratio * ring_buffer.maxlen:
                        # End of phrase
                        triggered = False
                        yield None
                        ring_buffer.clear()


class AudioStore(object):
    """Stores the current audio data being recognized, plus the last `maxlen` recognitions as tuples (audio, text, grammar_name, rule_name), indexed in reverse order (0 is most recent)"""

    def __init__(self, audio_obj, maxlen=0, save_dir=None, auto_save_predicate_func=None):
        self.audio_obj = audio_obj
        self.maxlen = maxlen
        self.save_dir = save_dir
        # if self.save_dir and not os.path.exists(self.save_dir): os.makedirs(self.save_dir)
        self.auto_save_predicate_func = auto_save_predicate_func
        self.deque = collections.deque(maxlen=maxlen) if maxlen > 0 else None
        self.blocks = []

    current_audio_data = property(lambda self: ''.join(self.blocks))

    def add_block(self, block):
        self.blocks.append(block)

    def finalize(self, text, grammar_name, rule_name):
        get_recognition = lambda: (self.current_audio_data, text, grammar_name, rule_name)
        if self.deque is not None:
            self.deque.appendleft(get_recognition())
        if self.auto_save_predicate_func and self.auto_save_predicate_func(*get_recognition()):
            self.save(0)
        self.blocks = []

    def save(self, index):
        if self.save_dir:
            filename = os.path.join(self.save_dir, "retain_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f") + ".wav")
            audio, text, grammar_name, rule_name = self.deque[index]
            self.audio_obj.write_wav(filename, audio)
            with open(os.path.join(self.save_dir, "retain.csv"), "a") as csvfile:
                csvfile.write(','.join([filename, '0', grammar_name, rule_name, text]) + '\n')

    def __getitem__(self, key):
        return self.deque[key]
    def __len__(self):
        return len(self.deque)
    def __bool__(self):
        return True
    def __nonzero__(self):
        return True
