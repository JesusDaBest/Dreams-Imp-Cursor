"""Exercise cursor handover without driving the desktop or hiding the system cursor."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

RUNTIME = Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(RUNTIME))
spec = importlib.util.spec_from_file_location('picker',RUNTIME/'app.py')
picker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(picker)

class PickerLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name)
        self.paths = patch.multiple(picker,STATE=self.state,READY=self.state/'ready.json',ERROR=self.state/'error.txt')
        self.paths.start()
        self.app=picker.App.__new__(picker.App)
        self.app.root=Mock();self.app.worker=None;self.app.log=None
        self.app.closing=False;self.app.changing=False;self.app.ready_seen=False
        self.app.grid_size=3;self.app.snap_job=None
        self.app.pending_character=None;self.app.active_character='00_default';self.app.cards={}
        self.app.selected='33_clown';self.app.settings={}
        self.app.config_path=self.state/'settings.json'
        self.app.by_id={'00_default':{'id':'00_default'},'33_clown':{'id':'33_clown'},'H21_Pag_Clown':{'id':'H21_Pag_Clown'}}
        self.app.signal_stop=Mock()
    def tearDown(self):
        if self.app.log:self.app.log.close()
        self.paths.stop();self.temp.cleanup()
    def test_clicking_a_card_explicitly_activates_that_imp(self):
        self.app.show=Mock();self.app.start=Mock();self.app.select('33_clown')
        self.app.show.assert_called_once_with('33_clown');self.app.start.assert_called_once_with()
        self.app.root.after.assert_not_called();self.app.signal_stop.assert_not_called()
    def test_card_click_during_handover_cannot_replace_pending_imp(self):
        self.app.changing=True;self.app.show=Mock();self.app.start=Mock()
        self.app.select('33_clown')
        self.app.show.assert_not_called();self.app.start.assert_not_called()
    def test_launching_app_only_schedules_polling(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            with patch.object(picker.App,'start') as start,patch.object(root,'after') as schedule:
                picker.App(root)
            start.assert_not_called()
            self.assertEqual([call.args[1].__name__ for call in schedule.call_args_list],['poll','poll_previews'])
        finally:root.destroy()
    def test_category_filter_does_not_activate_or_switch_the_cursor(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            with patch.object(picker.App,'start') as start:
                app=picker.App(root)
                app.group.set('Halloween')
                self.assertTrue(app.cards)
                self.assertTrue(all(picker.category(ident)=='Halloween' for ident in app.cards))
                start.assert_not_called()
        finally:root.destroy()
    def test_finger_drag_scrolls_without_selecting_an_imp(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            app=picker.App(root);app.start=Mock();app.grid_size=3
            with patch.object(app.gallery,'winfo_width',return_value=900),patch.object(app.gallery,'winfo_height',return_value=600):
                app.layout_cards()
            x,y=map(round,app.gallery.coords(next(iter(app.cards.values()))))
            before=app.gallery.yview()[0]
            app.press_gallery(SimpleNamespace(x=x,y=y))
            app.drag_gallery(SimpleNamespace(x=x,y=y-200))
            app.release_gallery(SimpleNamespace(x=x,y=y-200))
            self.assertGreater(app.gallery.yview()[0],before)
            app.start.assert_not_called()
        finally:root.destroy()
    def test_finger_tap_selects_only_on_release(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            app=picker.App(root);app.start=Mock();app.grid_size=3
            with patch.object(app.gallery,'winfo_width',return_value=900),patch.object(app.gallery,'winfo_height',return_value=600):
                app.layout_cards()
            ident,item=next(iter(app.cards.items()));x,y=map(round,app.gallery.coords(item))
            event=SimpleNamespace(x=x,y=y)
            app.press_gallery(event);app.start.assert_not_called()
            app.release_gallery(event)
            app.start.assert_called_once_with();self.assertEqual(app.selected,ident)
        finally:root.destroy()
    def test_mouse_wheel_scrolls_without_selecting_an_imp(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            app=picker.App(root);app.start=Mock();app.grid_size=3;app.layout_cards()
            before=app.gallery.yview()[0]
            app.scroll_cards(SimpleNamespace(delta=-120))
            self.assertGreater(app.gallery.yview()[0],before)
            app.start.assert_not_called()
        finally:root.destroy()
    def test_size_one_is_one_horizontal_row_and_swipe_does_not_activate(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            app=picker.App(root);app.start=Mock();app.grid_size=1
            with patch.object(app.gallery,'winfo_width',return_value=900),patch.object(app.gallery,'winfo_height',return_value=600):
                app.layout_cards()
            positions=[app.gallery.coords(item) for item in app.cards.values()]
            self.assertEqual(len({y for _,y in positions}),1)
            self.assertTrue(all(b[0]>a[0] for a,b in zip(positions,positions[1:])))
            x,y=map(round,positions[0]);before=app.gallery.xview()[0]
            app.press_gallery(SimpleNamespace(x=x,y=y))
            app.drag_gallery(SimpleNamespace(x=x-240,y=y+10))
            self.assertGreater(app.gallery.xview()[0],before)
            self.assertEqual(app.gallery.canvasy(0),0)
            app.release_gallery(SimpleNamespace(x=x-240,y=y+10))
            app.start.assert_not_called();app.cancel_snap()
        finally:root.destroy()
    def test_grid_button_cycles_all_sizes_without_changing_cursor(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            app=picker.App(root);app.start=Mock();app.grid_size=1
            actual=[]
            for _ in range(4):
                app.activate_control(('grid',None));actual.append(app.grid_size)
            self.assertEqual(actual,[2,3,4,1])
            self.assertEqual(json.loads(app.config_path.read_text())['grid_size'],1)
            app.start.assert_not_called()
        finally:root.destroy()
    def test_category_popup_filters_without_selecting_an_imp(self):
        root=picker.tk.Tk();root.withdraw()
        try:
            app=picker.App(root);app.start=Mock()
            app.activate_control(('category',None));self.assertTrue(app.menu_open)
            app.activate_control(('group','Halloween'))
            self.assertFalse(app.menu_open)
            self.assertTrue(all(picker.category(ident)=='Halloween' for ident in app.cards))
            app.start.assert_not_called()
        finally:root.destroy()
    def test_browsing_during_handover_keeps_the_explicitly_confirmed_imp(self):
        with patch.object(picker,'named_handle',return_value=True):self.app.start()
        self.assertEqual(self.app.pending_character,'33_clown')
        self.app.selected='H21_Pag_Clown'
        process=Mock(pid=123);process.poll.return_value=None
        with patch.object(picker,'named_handle',return_value=False),patch.object(picker.subprocess,'Popen',return_value=process) as launch:
            self.app.wait_then_launch(picker.time.monotonic()+5)
        args=launch.call_args.args[0]
        self.assertEqual(args[args.index('--character')+1],'33_clown')
        self.assertIn('--owner-pid',args)
        self.assertEqual(json.loads(self.app.config_path.read_text())['character'],'33_clown')
        self.assertEqual(self.app.selected,'H21_Pag_Clown')
    def test_clicking_active_imp_does_not_restart_it(self):
        self.app.worker=Mock();self.app.worker.poll.return_value=None
        self.app.selected=self.app.active_character
        self.app.start();self.app.signal_stop.assert_not_called()
    def test_old_renderer_must_exit_before_next_launch(self):
        self.app.worker=Mock();self.app.worker.poll.return_value=None
        with patch.object(picker,'named_handle',return_value=False),patch.object(picker.subprocess,'Popen') as launch:
            self.app.wait_then_launch(picker.time.monotonic()+5)
        launch.assert_not_called();self.app.root.after.assert_called_once()
    def test_stale_ready_file_is_not_an_acknowledgment(self):
        self.app.worker=Mock(pid=123);self.app.worker.poll.return_value=None
        (self.state/'ready.json').write_text(json.dumps({'pid':122,'character':'00_default'}))
        self.app.poll();self.assertFalse(self.app.ready_seen)
        (self.state/'ready.json').write_text(json.dumps({'pid':123,'character':'33_clown'}))
        self.app.poll();self.assertTrue(self.app.ready_seen)
    def test_quitting_requests_normal_exit_and_reaps_own_renderer(self):
        self.app.worker=Mock();self.app.worker.poll.return_value=None
        self.app.close()
        self.app.signal_stop.assert_called_once();self.app.worker.wait.assert_called_once_with(timeout=4)
        self.app.worker.terminate.assert_not_called();self.app.root.destroy.assert_called_once()

if __name__=='__main__':unittest.main()
