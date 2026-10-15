import os
import tempfile
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

from pondpet.app import COMPACT_SIZE, FULL_SIZE, DesktopPet


class NativeAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = DesktopPet(self.temp.name)
        pygame.event.clear()

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def events(self, *events):
        for event in events:
            pygame.event.post(event)
        self.app.handle_events()
        self.app.render()

    def key(self, key, mod=0):
        return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)

    def test_shortcut_does_not_leak_into_unicode_task(self):
        self.events(
            self.key(pygame.K_n),
            pygame.event.Event(pygame.TEXTINPUT, text="n"),
            pygame.event.Event(pygame.TEXTINPUT, text="写完一段文章"),
            self.key(pygame.K_RETURN),
        )
        self.assertEqual(self.app.model.tasks[0].text, "写完一段文章")
        self.assertEqual(self.app.draft, "")
        self.assertFalse(self.app.model.timer.running)

    def test_typing_space_does_not_start_the_focus_timer(self):
        self.app.action("task-input")
        self.events(self.key(pygame.K_SPACE), pygame.event.Event(pygame.TEXTINPUT, text=" "))
        self.assertEqual(self.app.draft, " ")
        self.assertFalse(self.app.model.timer.running)

    def test_paste_reads_unicode_once_and_normalizes_newlines(self):
        self.app.action("task-input")
        with patch("pondpet.app.read_text", return_value="读一章书\n然后休息") as clipboard:
            self.events(self.key(pygame.K_v, pygame.KMOD_META))
        clipboard.assert_called_once()
        self.assertEqual(self.app.draft, "读一章书 然后休息")

    def test_ime_enter_commits_before_submitting(self):
        self.app.action("task-input")
        self.events(pygame.event.Event(pygame.TEXTEDITING, text="写完"), self.key(pygame.K_RETURN))
        self.assertEqual(self.app.model.tasks, [])
        self.events(pygame.event.Event(pygame.TEXTINPUT, text="写完"), self.key(pygame.K_RETURN))
        self.assertEqual(self.app.model.tasks[0].text, "写完")

    def test_click_timer_and_protect_active_session_from_reset(self):
        self.events(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(310, 420)))
        self.assertTrue(self.app.model.timer.running)
        self.app.model.timer.remaining = 1200
        self.app.action("reset")
        self.app.action("duration:45")
        self.assertLessEqual(self.app.model.timer.remaining, 1200)
        self.assertEqual(self.app.model.timer.focus_minutes, 25)

    def test_compact_and_restore_preserve_tasks_and_running_timer(self):
        self.app.model.add_task("保留这一件")
        self.app.action("timer")
        self.app.action("compact")
        self.assertEqual(self.app.screen.get_size(), COMPACT_SIZE)
        self.assertTrue(self.app.model.timer.running)
        self.app.action("compact")
        self.assertEqual(self.app.screen.get_size(), FULL_SIZE)
        self.assertEqual(self.app.model.tasks[0].text, "保留这一件")

    def test_modal_traps_focus_and_escape_restores_the_main_view(self):
        self.app.action("settings")
        self.app.render()
        self.assertNotIn("timer", [control.key for control in self.app.ui.controls])
        self.events(self.key(pygame.K_TAB))
        self.assertTrue(self.app.keyboard_focus)
        self.assertIn(self.app.focus, [control.key for control in self.app.ui.controls])
        self.events(self.key(pygame.K_ESCAPE))
        self.assertIsNone(self.app.panel)
        self.assertIn("timer", [control.key for control in self.app.ui.controls])

    def test_complete_task_and_restart_from_actual_saved_file(self):
        self.app.model.add_task("一件小事")
        self.app.action("task:" + self.app.model.tasks[0].id)
        self.app.close()
        self.app = DesktopPet(self.temp.name)
        self.assertTrue(self.app.model.tasks[0].done)

    def test_reduced_motion_stops_all_ambient_effects(self):
        prefs = self.app.model.preferences
        prefs["rain"] = True
        for _ in range(200):
            self.app.garden.update(0.1, prefs)
        fish_before = [fish.copy() for fish in self.app.garden.fish]
        prefs["reduced_motion"] = True
        for _ in range(10):
            self.app.garden.update(0.1, prefs)
        self.assertEqual(self.app.garden.fish, fish_before)
        self.assertEqual(self.app.garden.rain, [])
        self.assertEqual(self.app.garden.ripples, [])

    def test_keyboard_can_reach_tasks_beyond_the_first_two_rows(self):
        for i in range(5):
            self.app.model.add_task(f"第 {i + 1} 件事")
        self.events(self.key(pygame.K_PAGEDOWN), self.key(pygame.K_PAGEDOWN))
        last_key = "task:" + self.app.model.tasks[-1].id
        self.assertIn(last_key, [control.key for control in self.app.ui.controls])
        self.app.focus = last_key
        self.app.keyboard_focus = True
        self.events(self.key(pygame.K_RETURN))
        self.assertTrue(self.app.model.tasks[-1].done)


if __name__ == "__main__":
    unittest.main()
