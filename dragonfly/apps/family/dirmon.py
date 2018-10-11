
import time
from six import string_types

import win32file, win32event
import win32con

import logging


#===========================================================================
# Internal container class representing a monitored directory.

class _Dir(object):

    __slots__= ("path", "handle", "overlapped")

    def __init__(self, path):
        if not isinstance(path, string_types):
            raise TypeError("Path argument must be a string/unicode object;"
                            " instead received %r" % (path,))
        self.path = path
        self.handle = win32file.CreateFile(
             self.path,
             0x0001,  # FILE_LIST_DIRECTORY
             win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
             None,
             win32con.OPEN_EXISTING,
             win32con.FILE_FLAG_BACKUP_SEMANTICS | win32con.FILE_FLAG_OVERLAPPED,
             None,
            )
        self.overlapped = win32file.OVERLAPPED()
        self.overlapped.hEvent = win32event.CreateEvent(None, True, 0, None)

    def is_modified(self, buffer):
        print("path", self.path)
        result = win32file.ReadDirectoryChangesW(
             self.handle,
             buffer,
             True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME 
              | win32con.FILE_NOTIFY_CHANGE_DIR_NAME
              | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES
              | win32con.FILE_NOTIFY_CHANGE_SIZE
              | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
              | win32con.FILE_NOTIFY_CHANGE_SECURITY,
             self.overlapped,
            )
        print("result  1", result)
        result = win32event.WaitForMultipleObjects([self.overlapped.hEvent], True, 0)
        print("result  2", result)
        if result != win32event.WAIT_TIMEOUT:
#            result = win32file.GetOverlappedResult(self.handle, self.overlapped, False)
            return True
        else:
            return False


#===========================================================================
# Directory monitor class.

class DirectoryMonitor(object):

    _log = logging.getLogger("dirmon")

    def __init__(self):
        self._buffer = win32file.AllocateReadBuffer(8192)
        self._directories = []

    def add_directories(self, *directories):
        """
            Add one or more directories to be monitored.

            Parameter:
              - directories (sequence of *str* or *unicode*) --
                the new directories to be monitored.

        """
        for path in directories:
            if path not in self.directories:
                try:
                    self._directories.append(_Dir(path))
                except Exception as e:
                    self._log.exception("Failed to monitor directory %r: %s"
                                        % (path, e))

    @property
    def directories(self):
        """ A sequence of paths to the monitored directories. """
        return tuple(d.path for d in self._directories)

    def is_modified(self):
        """ Return True if any of the monitored directories has changed. """
        for directory in self._directories:
            if directory.is_modified(self._buffer):
                return True
