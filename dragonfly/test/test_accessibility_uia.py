import unittest
import importlib
import os
import sys
import types

from dragonfly.accessibility import uia


class _FakeUIAConstants(object):
    UIA_TextPatternId = "text-pattern"
    UIA_ValuePatternId = "value-pattern"
    UIA_EditControlTypeId = "edit"
    UIA_DocumentControlTypeId = "document"
    TextPatternRangeEndpoint_Start = "start"
    TextPatternRangeEndpoint_End = "end"
    TextUnit_Character = "character"


class _FakeSelectionArray(object):

    def __init__(self, ranges):
        self._ranges = ranges
        self.Length = len(ranges)

    def GetElement(self, index):
        return self._ranges[index]


class _FakeTextRange(object):

    def __init__(self, text, start=0, end=None, selection_state=None):
        self._text = text
        self.start = start
        self.end = len(text) if end is None else end
        self._selection_state = selection_state if selection_state is not None else {"selected": None}

    @property
    def selected(self):
        return self._selection_state["selected"]

    def Clone(self):
        return _FakeTextRange(self._text, self.start, self.end, self._selection_state)

    def GetText(self, _max_count):
        return self._text[self.start:self.end]

    def MoveEndpointByUnit(self, endpoint, _unit, count):
        if endpoint == _FakeUIAConstants.TextPatternRangeEndpoint_Start:
            self.start += count
        else:
            self.end += count

    def MoveEndpointByRange(self, endpoint, other_range, other_endpoint):
        value = other_range.start if other_endpoint == _FakeUIAConstants.TextPatternRangeEndpoint_Start else other_range.end
        if endpoint == _FakeUIAConstants.TextPatternRangeEndpoint_Start:
            self.start = value
        else:
            self.end = value

    def Move(self, _unit, count):
        self.start += count
        self.end += count
        return count

    def CompareEndpoints(self, this_endpoint, other_range, other_endpoint):
        this_value = self.start if this_endpoint == _FakeUIAConstants.TextPatternRangeEndpoint_Start else self.end
        other_value = other_range.start if other_endpoint == _FakeUIAConstants.TextPatternRangeEndpoint_Start else other_range.end
        if this_value < other_value:
            return -1
        if this_value > other_value:
            return 1
        return 0

    def Select(self):
        self._selection_state["selected"] = (self.start, self.end)

    def GetBoundingRectangles(self):
        width = max(1, self.end - self.start)
        return [self.start, 10, width, 5]


class _FakeTextPattern(object):

    def __init__(self, text, selection_start):
        self.DocumentRange = _FakeTextRange(text, 0, len(text))
        self._selection = [_FakeTextRange(text, selection_start, selection_start)]

    def GetSelection(self):
        return _FakeSelectionArray(self._selection)


class _FakeValuePattern(object):

    def __init__(self, read_only):
        self.CurrentIsReadOnly = read_only


class _FakePatternWrapper(object):

    def __init__(self, value):
        self._value = value

    def QueryInterface(self, _interface):
        return self._value


class _FakeNullPattern(object):

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def QueryInterface(self, _interface):
        raise ValueError("NULL COM pointer access")


class _FakeFailingPattern(object):

    def __init__(self, text):
        self.DocumentRange = _FakeTextRange(text, 0, len(text))
        self._selection = [_FakeTextRange(text, 0, 0)]

    def GetSelection(self):
        return _FakeSelectionArray(self._selection)

    def QueryInterface(self, _interface):
        raise ValueError("already typed")


class _FakeElement(object):

    def __init__(self, patterns=None, control_type=None):
        self._patterns = patterns or {}
        self.CurrentControlType = control_type

    def GetCurrentPattern(self, pattern_id):
        return self._patterns.get(pattern_id)


class _FakeAutomation(object):

    def __init__(self, focused_element=None):
        self._focused_element = focused_element

    def GetFocusedElement(self):
        return self._focused_element


class _FakeOsController(object):

    def __init__(self, fail=False):
        if fail:
            raise RuntimeError("controller init failed")
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class AccessibilityUiaTestCase(unittest.TestCase):

    def setUp(self):
        self._old_uia = uia.UIA
        self._old_create_automation = getattr(uia, "_create_automation", None)
        self._old_load_uia_modules = getattr(uia, "_load_uia_modules", None)
        self._old_import_module = uia.importlib.import_module
        uia.UIA = _FakeUIAConstants

    def tearDown(self):
        uia.UIA = self._old_uia
        if self._old_create_automation is not None:
            uia._create_automation = self._old_create_automation
        if self._old_load_uia_modules is not None:
            uia._load_uia_modules = self._old_load_uia_modules
        uia.importlib.import_module = self._old_import_module

    def test_text_node_exposes_expanded_text_and_cursor(self):
        text_pattern = _FakeTextPattern("alpha beta", 6)

        node = uia.UiaAccessibleTextNode(None, text_pattern)

        self.assertEqual("alpha beta", node.expanded_text)
        self.assertEqual(6, node.cursor)

    def test_text_node_select_range_tracks_selected_offsets(self):
        text_pattern = _FakeTextPattern("alpha beta", 0)

        node = uia.UiaAccessibleTextNode(None, text_pattern)
        node.select_range(2, 5)

        self.assertEqual((2, 5), text_pattern.DocumentRange.selected)

    def test_text_node_sets_cursor_with_collapsed_selection(self):
        text_pattern = _FakeTextPattern("alpha beta", 0)

        node = uia.UiaAccessibleTextNode(None, text_pattern)
        node.set_cursor(4)

        self.assertEqual((4, 4), text_pattern.DocumentRange.selected)
        self.assertEqual(4, node.cursor)

    def test_text_node_returns_character_bounding_box(self):
        text_pattern = _FakeTextPattern("alpha beta", 0)

        node = uia.UiaAccessibleTextNode(None, text_pattern)
        box = node.get_bounding_box(3)

        self.assertEqual(3, box.x)
        self.assertEqual(10, box.y)
        self.assertEqual(1, box.width)
        self.assertEqual(5, box.height)

    def test_accessible_returns_text_node_when_text_pattern_present(self):
        text_pattern = _FakeTextPattern("alpha beta", 6)
        element = _FakeElement({
            _FakeUIAConstants.UIA_TextPatternId: text_pattern,
        })

        accessible = uia.Accessible(element)
        text_node = accessible.as_text()

        self.assertIsInstance(text_node, uia.UiaAccessibleTextNode)
        self.assertEqual("alpha beta", text_node.expanded_text)

    def test_accessible_uses_query_interface_wrapper_for_text_pattern(self):
        text_pattern = _FakeTextPattern("alpha beta", 6)
        element = _FakeElement({
            _FakeUIAConstants.UIA_TextPatternId: _FakePatternWrapper(text_pattern),
        })

        accessible = uia.Accessible(element)
        text_node = accessible.as_text()

        self.assertIsInstance(text_node, uia.UiaAccessibleTextNode)
        self.assertEqual(6, text_node.cursor)

    def test_accessible_ignores_null_text_pattern_pointer(self):
        element = _FakeElement({
            _FakeUIAConstants.UIA_TextPatternId: _FakeNullPattern(),
        })

        accessible = uia.Accessible(element)

        self.assertIsNone(accessible.as_text())

    def test_accessible_uses_pattern_directly_if_query_interface_fails(self):
        element = _FakeElement({
            _FakeUIAConstants.UIA_TextPatternId: _FakeFailingPattern("alpha beta"),
        })

        accessible = uia.Accessible(element)
        text_node = accessible.as_text()

        self.assertIsInstance(text_node, uia.UiaAccessibleTextNode)
        self.assertEqual("alpha beta", text_node.expanded_text)

    def test_accessible_reports_editable_from_value_pattern(self):
        element = _FakeElement({
            _FakeUIAConstants.UIA_ValuePatternId: _FakeValuePattern(False),
        })

        accessible = uia.Accessible(element)

        self.assertTrue(accessible.is_editable())

    def test_accessible_falls_back_to_control_type_for_editable(self):
        element = _FakeElement(control_type=_FakeUIAConstants.UIA_EditControlTypeId)

        accessible = uia.Accessible(element)

        self.assertTrue(accessible.is_editable())

    def test_accessible_ignores_null_value_pattern_pointer(self):
        element = _FakeElement({
            _FakeUIAConstants.UIA_ValuePatternId: _FakeNullPattern(),
        }, control_type=_FakeUIAConstants.UIA_DocumentControlTypeId)

        accessible = uia.Accessible(element)

        self.assertTrue(accessible.is_editable())

    def test_controller_requires_available_automation_backend(self):
        uia._load_uia_modules = lambda: (_ for _ in ()).throw(ImportError("missing uia"))

        with self.assertRaises(ImportError):
            uia.Controller()

    def test_load_uia_modules_generates_type_library_when_wrapper_missing(self):
        calls = []

        def fake_import_module(name):
            if name == "comtypes":
                return types.SimpleNamespace()
            if name == "comtypes.client":
                return types.SimpleNamespace(
                    GetModule=lambda path: calls.append(path)
                )
            if name == "comtypes.gen.UIAutomationClient":
                if not calls:
                    raise ImportError("wrapper missing")
                return _FakeUIAConstants
            raise ImportError(name)

        uia.importlib.import_module = fake_import_module

        _comtypes, client, uia_client = uia._load_uia_modules()

        self.assertEqual(["UIAutomationCore.dll"], calls)
        self.assertEqual(_FakeUIAConstants, uia_client)

    def test_controller_init_does_not_create_automation_until_context_initializes(self):
        calls = []
        uia._load_uia_modules = lambda: ("comtypes", "client", _FakeUIAConstants)
        uia._create_automation = lambda: calls.append("create") or _FakeAutomation()

        uia.Controller()

        self.assertEqual([], calls)

    def test_controller_start_surfaces_initialization_failure(self):
        uia._load_uia_modules = lambda: ("comtypes", "client", _FakeUIAConstants)
        uia._create_automation = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        controller = uia.Controller()

        with self.assertRaises(RuntimeError):
            controller.start()

    def test_controller_runs_closure_from_background_thread(self):
        old_start_blocking = uia.Controller._start_blocking

        def fake_start_blocking(controller):
            controller._startup_done_event.set()
            while not controller._shutdown_event.is_set():
                capture = controller._closure_queue.get()
                capture.return_value = capture.closure(controller._context)
                capture.done_event.set()
                controller._shutdown_event.set()

        try:
            uia._load_uia_modules = lambda: ("comtypes", "client", _FakeUIAConstants)
            uia.Controller._start_blocking = fake_start_blocking
            uia._create_automation = lambda: _FakeAutomation()
            controller = uia.Controller()
            controller._context = types.SimpleNamespace(marker="ok")
            controller.start()

            result = controller.run_sync(lambda context: context.marker)

            self.assertEqual("ok", result)
        finally:
            uia.Controller._start_blocking = old_start_blocking

    def test_context_update_focus_wraps_focused_element(self):
        text_pattern = _FakeTextPattern("alpha beta", 6)
        element = _FakeElement({
            _FakeUIAConstants.UIA_TextPatternId: text_pattern,
            _FakeUIAConstants.UIA_ValuePatternId: _FakeValuePattern(False),
        })
        uia._create_automation = lambda: _FakeAutomation(element)

        context = uia.Context()
        context.initialize()
        context.update_focus()

        self.assertIsInstance(context.focused, uia.Accessible)
        self.assertTrue(context.focused.is_editable())

    def test_windows_selector_prefers_uia_controller(self):
        accessibility = importlib.import_module("dragonfly.accessibility")
        old_platform = sys.platform
        old_display = os.environ.get("DISPLAY")
        old_uia = sys.modules.get("dragonfly.accessibility.uia")
        old_ia2 = sys.modules.get("dragonfly.accessibility.ia2")
        try:
            sys.platform = "win32"
            os.environ.pop("DISPLAY", None)
            sys.modules["dragonfly.accessibility.uia"] = types.SimpleNamespace(
                Controller=lambda: _FakeOsController()
            )
            sys.modules["dragonfly.accessibility.ia2"] = types.SimpleNamespace(
                Controller=lambda: _FakeOsController()
            )

            accessibility = importlib.reload(accessibility)
            controller = accessibility.get_accessibility_controller()

            self.assertIsInstance(controller.os_controller, _FakeOsController)
        finally:
            sys.platform = old_platform
            if old_display is None:
                os.environ.pop("DISPLAY", None)
            else:
                os.environ["DISPLAY"] = old_display
            if old_uia is None:
                sys.modules.pop("dragonfly.accessibility.uia", None)
            else:
                sys.modules["dragonfly.accessibility.uia"] = old_uia
            if old_ia2 is None:
                sys.modules.pop("dragonfly.accessibility.ia2", None)
            else:
                sys.modules["dragonfly.accessibility.ia2"] = old_ia2
            importlib.reload(accessibility)

    def test_windows_selector_falls_back_to_ia2_when_uia_init_fails(self):
        accessibility = importlib.import_module("dragonfly.accessibility")
        old_platform = sys.platform
        old_display = os.environ.get("DISPLAY")
        old_uia = sys.modules.get("dragonfly.accessibility.uia")
        old_ia2 = sys.modules.get("dragonfly.accessibility.ia2")
        try:
            sys.platform = "win32"
            os.environ.pop("DISPLAY", None)
            sys.modules["dragonfly.accessibility.uia"] = types.SimpleNamespace(
                Controller=lambda: _FakeOsController(fail=True)
            )
            sys.modules["dragonfly.accessibility.ia2"] = types.SimpleNamespace(
                Controller=lambda: _FakeOsController()
            )

            accessibility = importlib.reload(accessibility)
            controller = accessibility.get_accessibility_controller()

            self.assertIsInstance(controller.os_controller, _FakeOsController)
            self.assertTrue(controller.os_controller.started)
        finally:
            sys.platform = old_platform
            if old_display is None:
                os.environ.pop("DISPLAY", None)
            else:
                os.environ["DISPLAY"] = old_display
            if old_uia is None:
                sys.modules.pop("dragonfly.accessibility.uia", None)
            else:
                sys.modules["dragonfly.accessibility.uia"] = old_uia
            if old_ia2 is None:
                sys.modules.pop("dragonfly.accessibility.ia2", None)
            else:
                sys.modules["dragonfly.accessibility.ia2"] = old_ia2
            importlib.reload(accessibility)

    def test_windows_selector_does_not_return_stopped_instance_when_reinit_fails(self):
        accessibility = importlib.import_module("dragonfly.accessibility")
        old_controller_instance = accessibility.controller_instance
        old_classes = accessibility.os_controller_classes

        class _StoppedController(object):
            stopped = True

        class _FailingController(object):

            def __init__(self):
                raise RuntimeError("reinit failed")

        try:
            accessibility.controller_instance = _StoppedController()
            accessibility.os_controller_classes = [_FailingController]

            controller = accessibility.get_accessibility_controller()

            self.assertIsNone(controller)
            self.assertIsNone(accessibility.controller_instance)
        finally:
            accessibility.controller_instance = old_controller_instance
            accessibility.os_controller_classes = old_classes


if __name__ == "__main__":
    unittest.main()
