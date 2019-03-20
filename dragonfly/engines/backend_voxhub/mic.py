import pyaudio


def test_microphone():
    pa = pyaudio.PyAudio()  # prints a lot of junk

    print ""
    print "LISTING OF ALL INPUT DEVICES SUPPORTED BY PORTAUDIO"
    print "(any device numbers not shown are for output only)"
    print ""

    for i in range(0, pa.get_device_count()):
        info = pa.get_device_info_by_index(i)

        if info['maxInputChannels'] > 0:  # microphone? or just speakers
            print "DEVICE #%d" % info['index']
            print "    %s" % info['name']
            print "    input channels = %d, output channels = %d, defaultSampleRate = %d" \
                % (info['maxInputChannels'], info['maxOutputChannels'], info['defaultSampleRate'])
            print info


def setup_microphone(mic, byte_rate, chunk):
    pa = pyaudio.PyAudio()
    stream = None

    while stream is None:
        try:
            # try adjusting this if you want fewer network packets

            mic = mic
            if mic == -1:
                mic = pa.get_default_input_device_info()['index']
                print "Selecting default mic"
            print "Using mic #", mic
            stream = pa.open(
                rate=byte_rate,
                format=pyaudio.paInt16,
                channels=1,
                input=True,
                input_device_index=mic,
                frames_per_buffer=chunk)
            return stream
        except IOError, e:
            if (e.errno == -9997 or e.errno == 'Invalid sample rate'):
                new_sample_rate = int(pa.get_device_info_by_index(mic)['defaultSampleRate'])
                if byte_rate != new_sample_rate:
                    byte_rate = new_sample_rate
                    continue
            print str(e)
            print "\nCould not open microphone. Please try a different device."
            return False


if __name__ == "__main__":
    test_microphone()