# Silvius microphone client based on Tanel's client.py
__author__ = 'dwk'
import threading
import sys
import urllib
import json
import audioop
import time


from ws4py.client.threadedclient import WebSocketClient
from dragonfly.engines.backend_voxhub.config import *
from dragonfly.engines.backend_voxhub.mic import setup_microphone

reconnect_mode = False
fatal_error = False


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
        mic_stream = setup_microphone(self.mic, self.byte_rate, self.chunk)
        if not mic_stream:
            global fatal_error
            fatal_error = True
            return

        def mic_to_ws():  # uses stream
            try:
                print "\nLISTENING TO MICROPHONE"
                while True:
                    data = mic_stream.read(self.chunk)
                    if self.audio_gate > 0:
                        rms = audioop.rms(data, 2)
                        if rms < self.audio_gate:
                            data = '\00' * len(data)

                    self.send_data(data)
            except IOError, e:
                # usually a broken pipe
                print e
            except AttributeError:
                # currently raised when the socket gets closed by main thread
                pass

            try:
                self.close()
            except IOError:
                pass

        threading.Thread(target=mic_to_ws).start()

    def received_message(self, m):  # TODO : Discuss with David
        response = json.loads(str(m))
        #print >> sys.stderr, "RESPONSE:", response
        if response['status'] == 0:
            if 'result' in response:
                trans = response['result']['hypotheses'][0]['transcript']
                if response['result']['final']:
                    if self.show_hypotheses:
                        print >> sys.stderr, '\r%s' % trans.replace("\n", "\\n")
                    # print '%s' % trans.replace("\n", "\\n")  # final result!
                    self.queue.put(trans.replace("\n", "\\n"))
                    # sys.stdout.flush()
                elif self.show_hypotheses:
                    print_trans = trans.replace("\n", "\\n")
                    if len(print_trans) > 80:
                        print_trans = "... %s" % print_trans[-75:],
                    print >> sys.stderr, '\r%s' % print_trans,
            # if 'adaptation_state' in response:
            #     if self.save_adaptation_state_filename:
            #         print >> sys.stderr, "Saving adaptation state to %s" % self.save_adaptation_state_filename
            #         with open(self.save_adaptation_state_filename, "w") as f:
            #             f.write(json.dumps(response['adaptation_state']))
        else:
            print >> sys.stderr, "Received error from server (status %d)" % response['status']
            if 'message' in response:
                print >> sys.stderr, "Error message:",  response['message']
            
            global reconnect_mode
            if reconnect_mode:
                print >> sys.stderr, "Sleeping for five seconds before reconnecting"
                time.sleep(5)


def connect_to_server(queue=None):
    uri = create_connection_uri()
    print >> sys.stderr, "Connecting to", uri

    ws = MyClient(uri, byte_rate=MISC_CONFIG["byte_rate"], mic=MISC_CONFIG["device"],
                  show_hypotheses=MISC_CONFIG["hypotheses"],
                  save_adaptation_state_filename=MISC_CONFIG.get("save_adaptation_state", None),
                  send_adaptation_state_filename=MISC_CONFIG.get("send_adaptation_state", None),
                  audio_gate=MISC_CONFIG["audio_gate"], chunk=MISC_CONFIG['chunk'],
                  queue=queue)
    ws.connect()
    ws.run_forever()


def create_connection_uri():
    uri = "ws://%s:%s/%s?%s" % (SERVER, PORT, PATH, urllib.urlencode([("content-type", CONTENT_TYPE)]))
    return uri
