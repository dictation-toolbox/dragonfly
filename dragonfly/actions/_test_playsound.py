
from time import sleep
from dragonfly import *
import winsound


class PlaySound(ActionBase):

    def __init__(self, name=None, file=None):
        ActionBase.__init__(self)
        if name is not None:
            self._name = name
            self._flags = winsound.SND_ASYNC | winsound.SND_ALIAS
        elif file is not None:
            self._name = file
            self._flags = winsound.SND_ASYNC | winsound.SND_FILENAME

        self._str = str(self._name)

    def _execute(self, data=None):
        winsound.PlaySound(self._name, self._flags)


# See for more sound names:
# http://www.python.org/doc/2.5.2/lib/module-winsound.html
PlaySound("SystemHand").execute()
sleep(1)
PlaySound(file=r"C:\WINDOWS\Media\Windows XP Battery Low.wav").execute()
sleep(1)
