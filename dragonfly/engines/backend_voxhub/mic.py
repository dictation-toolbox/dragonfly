import pyaudio
import audioop
import threading

class VoxhubMicrophoneManager:
    @staticmethod
    def dump_list():
        pa = pyaudio.PyAudio()  # prints a lot of junk

        print ""
        print "LISTING OF ALL INPUT DEVICES SUPPORTED BY PORTAUDIO."
        print "Device can be configured by adding <DEVICE_NUMBER> under device in backend_voxhub/config.py"
        print "(any device numbers not shown are for output only)"
        print ""

        for i in range(0, pa.get_device_count()):
            info = pa.get_device_info_by_index(i)

            if info['maxInputChannels'] > 0:  # microphone? or just speakers
                print "DEVICE_NUMBER = %d" % info['index']
                print "    %s" % info['name']
                print "    input channels = %d, output channels = %d, defaultSampleRate = %d" \
                    % (info['maxInputChannels'], info['maxOutputChannels'], info['defaultSampleRate'])
                #print info

    @staticmethod
    def open(mic_index, byte_rate, chunk):
        pa = pyaudio.PyAudio()
        stream = None
        original_byte_rate = byte_rate

        while stream is None:
            try:
                if mic_index == -1:
                    mic_index = pa.get_default_input_device_info()['index']
                    print "Selecting default mic"
                print "Using mic #", mic_index
                stream = pa.open(
                    rate        = byte_rate,
                    format      = pyaudio.paInt16,
                    channels    = 1,
                    input       = True,
                    input_device_index = mic_index,
                    frames_per_buffer  = chunk)
                print "Creating microphone with", byte_rate, stream
                return VoxhubMicrophone(original_byte_rate, byte_rate, stream, chunk)
            except IOError, e:
                if e.errno == -9997 or e.errno == 'Invalid sample rate':
                    new_sample_rate = int(pa.get_device_info_by_index(mic_index)['defaultSampleRate'])
                    if byte_rate != new_sample_rate:
                        byte_rate = new_sample_rate
                        continue
                print str(e)
                print "\nCould not open microphone. Please try a different device."
                return None

class VoxhubMicrophone:
    def __init__(self, original_byte_rate, byte_rate, stream, chunk):
        self.original_byte_rate = original_byte_rate
        self.byte_rate = byte_rate
        self.stream = stream
        self.chunk = chunk
        self.audio_gate = 0

    def set_audio_gate(self, gate):
        self.audio_gate = gate

    def start_thread(self, data_callback, finished_callback=None):
        print "Starting microphone thread..."
        def listen_to_mic():  # uses self.stream
            try:
                print "\nLISTENING TO MICROPHONE"
                last_state = None
                while True:
                    data = self.stream.read(self.chunk * self.byte_rate / self.original_byte_rate)
                    if self.audio_gate > 0:
                        rms = audioop.rms(data, 2)
                        if rms < self.audio_gate:
                            data = '\00' * len(data)
                    if self.byte_rate != self.original_byte_rate:
                        (data, last_state) = audioop.ratecv(data, 2, 1, sample_rate, self.byterate, last_state)

                    data_callback(data)
            except IOError, e:
                # usually a broken pipe
                print e
            except AttributeError:
                # currently raised when the socket gets closed by main thread
                pass

            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass

            try:
                if finished_callback:
                    finished_callback()
            except IOError:
                pass

        threading.Thread(target=listen_to_mic).start()
