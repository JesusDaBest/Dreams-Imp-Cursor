"""Reproduce the reported Windows input-access failure without accessing a protected desktop."""
import ctypes as C
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec=importlib.util.spec_from_file_location('overlay',Path(__file__).resolve().parents[1]/'runtime/win-imp-overlay.py')
overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)

class DesktopAccess(unittest.TestCase):
    def setUp(self):
        self.o=overlay.Overlay.__new__(overlay.Overlay)
        self.o.win=Mock();self.o.kernel=Mock();self.o.visible=True
        self.o.window=99;self.o.pos=overlay.W.POINT(100,200);self.o.stop_event=123
        self.o.arrow_hidden=True;self.o.hidden_roles={overlay.ARROW};self.o.input_available=True
        self.o.roles={99:overlay.ARROW};self.o.replace_arrow=True;self.o.menu_event=1
        self.o.swapped_buttons=False;self.o.check_cursor_at=1e30
        self.o.win.PeekMessageW.return_value=0;self.o.kernel.WaitForSingleObject.return_value=258
        self.o.win.GetAsyncKeyState.return_value=0
        self.o.win.GetCursorInfo.return_value=0
        self.restore=patch.object(overlay,'restore_cursor',return_value=True)
        self.restored=self.restore.start();C.set_last_error(5)
    def tearDown(self):self.restore.stop();C.set_last_error(0)
    def test_denied_cursor_info_yields_without_reading_position_or_keys(self):
        state=self.o.state()
        self.assertFalse(state.visible);self.assertFalse(self.o.input_available)
        self.o.win.GetCursorPos.assert_not_called();self.o.win.GetAsyncKeyState.assert_not_called()
        self.o.win.ShowWindow.assert_called_once_with(99,0);self.restored.assert_called_once()
    def test_render_does_not_touch_windows_cursor_while_access_is_denied(self):
        self.o.state();self.o._start_cursor_guard=Mock()
        self.o.present(None,(100,200),(0,0),True)
        self.o._start_cursor_guard.assert_not_called();self.o.win.UpdateLayeredWindow.assert_not_called()
    def test_resumes_on_successful_read_using_the_same_api(self):
        self.o.state()
        def allow(p):p._obj.cursor=99;p._obj.flags=1;return 1
        self.o.win.GetCursorInfo.side_effect=allow;self.o.win.GetCursorPos.return_value=1
        state=self.o.state()
        self.assertTrue(self.o.input_available);self.assertEqual(state.role,overlay.ARROW)
        self.assertEqual((state.x,state.y),(100,200))
        self.assertFalse(state.primary);self.assertEqual(state.menu_event,0)
    def test_denied_position_read_also_yields(self):
        self.o.win.GetCursorInfo.return_value=1;self.o.win.GetCursorPos.return_value=0
        self.assertFalse(self.o.state().visible);self.assertFalse(self.o.input_available)
    def test_other_api_errors_are_not_silenced(self):
        C.set_last_error(87)
        with self.assertRaises(OSError):self.o.state()
    def test_stop_still_works_while_desktop_is_unavailable(self):
        self.o.input_available=False;self.o.kernel.WaitForSingleObject.return_value=0
        self.assertIsNone(self.o.state());self.o.win.GetCursorInfo.assert_not_called()

if __name__=='__main__':unittest.main()
