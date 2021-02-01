"""
Window class for Talon
============================================================================

"""

# pylint: disable=E0401

from talon import ui
from .base_window import BaseWindow
from .rectangle import Rectangle


class TalonWindow(BaseWindow):
    """
        The Window class is an interface to the macOS window control and
        placement.

    """

    #-----------------------------------------------------------------------
    # Class methods to create new Window objects.

    @classmethod
    def get_foreground(cls):
        return cls.get_window(ui.active_window())

    @classmethod
    def get_all_windows(cls):
        return [cls.get_window(win) for win in ui.windows()]

    #-----------------------------------------------------------------------
    # Methods for initialization and introspection.

    def __init__(self, win):
        super().__init__(win.id)
        self._window = win

    def __repr__(self):
        return str(self._window)

    #-----------------------------------------------------------------------
    # Methods and properties for window attributes.

    def _get_window_text(self):
        return self._window.title

    def _get_class_name(self):
        return ''

    def _get_window_module(self):
        return self._window.app.name

    def _get_window_pid(self):
        return self._window.app.pid

    @property
    def is_minimized(self):
        return self._window.hidden # FIXME

    @property
    def is_maximized(self):
        return False # FIXME

    @property
    def is_visible(self):
        return not self._window.hidden

    #-----------------------------------------------------------------------
    # Methods related to window geometry.

    def get_position(self):
        rect = self._window.rect
        return Rectangle(rect.x, rect.y, rect.width, rect.height)

    def set_position(self, rectangle):
        assert isinstance(rectangle, Rectangle)
        self._window.rect = ui.Rect(rectangle.x, rectangle.y, rectangle.dx, rectangle.dy)

    #-----------------------------------------------------------------------
    # Methods for miscellaneous window control.

    def minimize(self):
        raise NotImplementedError

    def maximize(self):
        raise NotImplementedError

    def full_screen(self):
        raise NotImplementedError

    def restore(self):
        # Toggle maximized/minimized state if necessary.
        if self.is_maximized:
            return self.maximize()

        if self.is_minimized:
            return self.minimize()

        return True

    def close(self):
        raise NotImplementedError

    def set_foreground(self):
        self._window.focus()

    def set_focus(self):
        self._window.focus()
