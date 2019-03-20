# This Python file uses the following encoding: utf-8

"""
VoxhubEngine engine configuration module.
"""

# Speech-recognition server (Default: localhost)
SERVER = "silvius-server.voxhub.io"

# Server port
PORT = "8019"

# Use the specified content type (default is " + content_type + ")"
CONTENT_TYPE = "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1"

# Default path to access in server
PATH = 'client/ws/speech'

MISC_CONFIG = {
                'device': -1,                       # Select a different microphone (give device ID)
                'keep_going': False,                # Keep reconnecting to the server after periods of silence
                'hypotheses': True,                 # Show partial recognition hypotheses (default: True)
                'audio_gate': 0,                    # Audio-gate level to reduce detections when not talking
                'byte_rate': 16000,                 # Rate in bytes/sec at which audio should be sent to the server.
                'send_adaptation_state': None,      # Send adaptation state from file
                'save_adaptation_state': None,      # Save adaptation state to file
                'chunk': 2048 * 2                   # Try adjusting this if you want fewer network packets # TODO : Discuss with David
              }

