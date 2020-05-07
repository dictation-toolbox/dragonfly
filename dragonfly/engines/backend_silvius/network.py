from __future__ import print_function

# Silvius microphone client based on Tanel's client.py
__author__ = 'dwk'

import json
import sys
import time

try:
    from urllib import urlencode
except ImportError:  # for Python 3 and above
    from urllib.parse import urlencode

from ws4py.client.threadedclient import WebSocketClient

from .config import *
from .microphone import *

reconnect_mode = True
fatal_error = False


class SilviusAudioProcess:
    # This is meant to be invoked from a separate process. It loops forever.
    @staticmethod
    def connect_to_server(queue=None):
        uri = SilviusAudioProcess.create_connection_uri()

        while True:
            print("Connecting to", uri, file=sys.stderr)
            ws = MyClient(uri, byte_rate=MISC_CONFIG["byte_rate"],
                mic=SilviusMicrophoneManager.lookup_microphone(MISC_CONFIG["device"]),
                show_hypotheses=MISC_CONFIG["hypotheses"],
                save_adaptation_state_filename=MISC_CONFIG.get("save_adaptation_state", None),
                send_adaptation_state_filename=MISC_CONFIG.get("send_adaptation_state", None),
                audio_gate=MISC_CONFIG["audio_gate"], chunk=MISC_CONFIG['chunk'],
                queue=queue)
            ws.connect()
            ws.run_forever()

    @staticmethod
    def create_connection_uri():
        uri = "ws://%s:%s/%s?%s" % (SERVER, PORT, PATH, urlencode([("content-type", CONTENT_TYPE)]))
        return uri

class MyClient(WebSocketClient):

    def __init__(self, url, mic=1, protocols=None, extensions=None, heartbeat_freq=None, byte_rate=16000,
                 show_hypotheses=True,
                 save_adaptation_state_filename=None, send_adaptation_state_filename=None, audio_gate=0, chunk=0,
                 queue=None):
        super(MyClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.mic = mic
        self.show_hypotheses = show_hypotheses
        self.byte_rate = byte_rate
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename
        self.chunk = chunk
        self.audio_gate = audio_gate
        self.queue = queue

    def send_data(self, data):
        self.send(data, binary=True)

    def opened(self):
        mic = SilviusMicrophoneManager.open(self.mic, self.byte_rate, self.chunk)
        if not mic:
            global fatal_error
            fatal_error = True
            return

        def try_send_data(data):
            try:
                self.send_data(data)
                return True
            except IOError as e:
                # usually a broken pipe
                print(e)
            except AttributeError:
                # currently raised when the socket gets closed by main thread
                pass
            return False

        def skip_io_error(invoke):
            try:
                invoke()
            except IOError:
                pass

        try:
            mic.set_audio_gate(self.audio_gate)
            mic.start_thread(
                try_send_data,
                lambda : skip_io_error(self.close))
        except Exception as e:
            print(e)

    def received_message(self, m):
        response = json.loads(str(m))
        #print("RESPONSE:", response, file=sys.stderr)
        if response['status'] == 0:
            if 'result' in response:
                trans = response['result']['hypotheses'][0]['transcript']
                if response['result']['final']:
                    if self.show_hypotheses:
                        print('\r%s' % trans.replace("\n", "\\n"), file=sys.stderr)
                    # print('%s' % trans.replace("\n", "\\n"))  # final result!
                    self.queue.put(trans.replace("\n", "\\n"))
                    # sys.stdout.flush()
                elif self.show_hypotheses:
                    print_trans = trans.replace("\n", "\\n")
                    if len(print_trans) > 80:
                        print_trans = "... %s" % print_trans[-75:],
                    print('\r%s' % print_trans, end=' ', file=sys.stderr)
            # if 'adaptation_state' in response:
            #     if self.save_adaptation_state_filename:
            #         print("Saving adaptation state to %s" % self.save_adaptation_state_filename, file=sys.stderr)
            #         with open(self.save_adaptation_state_filename, "w") as f:
            #             f.write(json.dumps(response['adaptation_state']))
        else:
            print("Received error from server (status %d)" % response['status'], file=sys.stderr)
            if 'message' in response:
                print("Error message:",  response['message'], file=sys.stderr)
            
            global reconnect_mode
            if reconnect_mode:
                print("Sleeping for five seconds before reconnecting", file=sys.stderr)
                time.sleep(5)
