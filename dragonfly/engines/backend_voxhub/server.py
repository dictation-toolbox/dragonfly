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

            # to voluntarily close the connection, we would use
            #self.send_data("")
            #self.send("EOS")

            try:
                self.close()
            except IOError:
                pass

        threading.Thread(target=mic_to_ws).start()

    def received_message(self, m):  # TODO : Discuss with David
        response = json.loads(str(m))
        #print >> sys.stderr, "RESPONSE:", response
        #print >> sys.stderr, "JSON was:", m
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
                        print_trans = "... %s" % print_trans[-76:]
                    print >> sys.stderr, '\r%s' % print_trans,
            if 'adaptation_state' in response:
                if self.save_adaptation_state_filename:
                    print >> sys.stderr, "Saving adaptation state to %s" % self.save_adaptation_state_filename
                    with open(self.save_adaptation_state_filename, "w") as f:
                        f.write(json.dumps(response['adaptation_state']))
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
                  save_adaptation_state_filename=MISC_CONFIG["save_adaptation_state"],
                  send_adaptation_state_filename=MISC_CONFIG["send_adaptation_state"],
                  audio_gate=MISC_CONFIG["audio_gate"], chunk=MISC_CONFIG['chunk'],
                  queue=queue)
    ws.connect()
    ws.run_forever()


def create_connection_uri():
    uri = "ws://%s:%s/%s?%s" % (SERVER, PORT, PATH, urllib.urlencode([("content-type", CONTENT_TYPE)]))
    return uri

# TODO : Remove after asking David
# import argparse
# def setup(server="localhost", queue=None):
#     content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1"
#     path = 'client/ws/speech'
#
#     parser = argparse.ArgumentParser(description='Microphone client for silvius')
#     parser.add_argument('-s', '--server', default=server, dest="server", help="Speech-recognition server")
#     parser.add_argument('-p', '--port', default="8019", dest="port", help="Server port")
#     #parser.add_argument('-r', '--rate', default=16000, dest="rate", type=int, help="Rate in bytes/sec at which audio should be sent to the server.")
#     parser.add_argument('-d', '--device', default="-1", dest="device", type=int, help="Select a different microphone (give device ID)")
#     parser.add_argument('-k', '--keep-going', action="store_true", help="Keep reconnecting to the server after periods of silence")
#     parser.add_argument('--save-adaptation-state', help="Save adaptation state to file")
#     parser.add_argument('--send-adaptation-state', help="Send adaptation state from file")
#     parser.add_argument('--content-type', default=content_type, help="Use the specified content type (default is " + content_type + ")")
#     parser.add_argument('--hypotheses', default=True, type=int, help="Show partial recognition hypotheses (default: 1)")
#     parser.add_argument('-g', '--audio-gate', default=0, type=int, help="Audio-gate level to reduce detections when not talking")
#     args = parser.parse_args()
#     print >> sys.stderr, "ARGS",args.__dict__
#     content_type = args.content_type
#     print >> sys.stderr, "Content-Type:", content_type
#
#     if(args.keep_going):
#         global reconnect_mode
#         global fatal_error
#         reconnect_mode = True
#         while(fatal_error == False):
#             print >> sys.stderr, "Reconnecting..."
#             run(args, content_type, path, queue)
#     else:
#         run(args, content_type, path, queue)
#
# def run(args, content_type, path, queue):
#     uri = "ws://%s:%s/%s?%s" % (args.server, args.port, path, urllib.urlencode([("content-type", content_type)]))
#     print >> sys.stderr, "Connecting to", uri
#     print args.__dict__
#
#     ws = MyClient(uri, byterate=16000, mic=args.device, show_hypotheses=args.hypotheses,
#                   save_adaptation_state_filename=args.save_adaptation_state, send_adaptation_state_filename=args.send_adaptation_state, audio_gate=args.audio_gate, queue=queue)
#     ws.connect()
#     #result = ws.get_full_hyp()
#     #print result.encode('utf-8')
#     ws.run_forever()
#
# def main():
#     try:
#         setup()
#     except KeyboardInterrupt:
#         print >> sys.stderr, "\nexiting..."
#
# if __name__ == "__main__":
#     main()

