#!/usr/bin/python
# encoding: utf-8

"""
Script to test the Key and Text action on X11 using the "xev" program.

There should be two lines printed for each key press: a down event and
an up event. Each line will contain the key symbol (e.g. Return).
There will be a small delay per key press for both test actions to help view
the output from "xev" as the keys are pressed.

X11Errors may be logged for keys remapped or not mapped by xkb.
"""

from __future__ import print_function

import subprocess
import sys
import threading
import time
import logging

from dragonfly import Key, Text

logging.basicConfig()

XEV_PATH = "/usr/bin/xev"


def main():
    # Define keys to type.
    keys = []
    alphas = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    keys.extend(alphas)
    keys.extend(digits)

    # Add common symbol characters. Use long names for reserved characters.
    symbols = "!@#%^&*()_+`~[]{}|\\;'\".<>?="
    keys.extend(symbols)
    keys.extend(["comma", "colon", "minus", "slash", "space"])

    # Add virtual keys. Some keys are repeated purposefully to maintain key
    # state (e.g. caps lock).
    keys.extend([
        # Whitespace and editing keys
        "enter", "tab", "space", "backspace", "delete",

        # Special keys
        "escape", "insert", "insert", "pause", "apps",

        # Lock keys
        "scrolllock", "scrolllock", "numlock", "numlock", "capslock",
        "capslock",

        # Navigation keys
        "up", "down", "left", "right", "pageup", "pagedown", "home", "end",

        # Number pad keys
        "npmul", "npadd", "npsub", "npdec", "npdiv", "npsep", "np0", "np1",
        "np2", "np3", "np4", "np5", "np6", "np7", "np8", "np9",

        # Function keys
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11",
        "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19",
        "f20", "f21", "f22", "f23", "f24",

        # Multimedia keys (press toggle keys twice)
        "volumeup", "volup", "volumedown", "voldown", "volumemute",
        "volmute", "tracknext", "trackprev", "playpause", "playpause",
        "browserback", "browserforward",

        # Include some keys not defined in typeables.py. There are a lot of
        # these in X11. The first two are browser-specific media keys. The
        # others are the Cyrillic л and Japanese ぁ letters.
        "XF86Refresh", "XF86HomePage", "Cyrillic_el", "U3041",

        # Modifiers.
        "shift:down", "shift:up",
        "ctrl:down", "ctrl:up",
        "alt:down", "alt:up",
        "rshift:down", "rshift:up",
        "rctrl:down", "rctrl:up",
        "ralt:down", "ralt:up",
        "win:down", "win:up", "win:down", "win:up",
        "rwin:down", "rwin:up", "rwin:down", "rwin:up",

        # Some common key combinations.
        "s-insert",
        "c-left",
        "c-home",
        "a-f",
        "c-a",
    ])

    # Define text to type using all alphanumeric characters and valid
    # symbols. Also test some Unicode characters.
    other_symbols = u"é—…ôêěèźżėфй№😱ß°⌷⅕€¨§™ぁ"
    text = alphas + digits + symbols + ",:-/ \n\t" + other_symbols

    # Start xev and selectively print lines from it in the background.
    # Exit if the command fails.
    try:
        proc = subprocess.Popen(XEV_PATH,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        def print_key_events():
            for line in iter(proc.stdout.readline, b''):
                line = line.decode('utf-8')
                if "keysym" in line:
                    print(line.strip())

        t = threading.Thread(target=print_key_events)
        t.setDaemon(True)  # make this thread terminate with the main thread
        t.start()
    except Exception as e:
        print("Couldn't start xev: %s" % e, file=sys.stderr)
        exit(1)

    # Wait a few seconds before beginning.
    print("Please ensure xev is focused...")
    time.sleep(5)

    print("--------------------Starting Key tests--------------------")
    keys.extend(other_symbols)
    Key("/10,".join(keys)).execute()
    print("Done.")

    print("--------------------Starting Text tests-------------------")
    Text(text, pause=0.1).execute()
    print("Done.")

    print("Stopping xev.")
    proc.terminate()


if __name__ == '__main__':
    main()
