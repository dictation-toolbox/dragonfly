from time import sleep

from dragonfly import PlaySound

# See for more sound names:
# http://www.python.org/doc/2.5.2/lib/module-winsound.html
PlaySound("SystemHand").execute()
sleep(1)
PlaySound(file=r"C:\WINDOWS\Media\Windows XP Battery Low.wav").execute()
sleep(1)
