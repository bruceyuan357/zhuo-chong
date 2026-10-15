import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from pondpet.model import Companion, FocusTimer
from pondpet.storage import StateStore


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FocusTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.model = Companion(clock=self.clock, today=lambda: date(2026, 10, 15))

    def test_pause_excludes_idle_time_and_restart_stays_paused(self):
        timer = self.model.timer
        timer.toggle()
        self.clock.advance(65.25)
        self.model.update()
        timer.toggle()
        self.clock.advance(600)
        self.model.update()
        self.assertAlmostEqual(timer.remaining, 1434.75)
        restored = Companion(self.model.snapshot(), clock=self.clock)
        self.assertFalse(restored.timer.running)
        self.clock.advance(300)
        restored.update()
        self.assertAlmostEqual(restored.timer.remaining, 1434.75)
        restored.timer.toggle()
        self.clock.advance(1)
        restored.update()
        self.assertAlmostEqual(restored.timer.remaining, 1433.75)

    def test_large_time_jump_completes_once_and_does_not_auto_start_break(self):
        self.model.timer.toggle()
        self.clock.advance(60 * 60)
        self.assertEqual(self.model.update(), ("focus", 1500.0))
        self.assertEqual(self.model.today_stats, {"minutes": 25, "sessions": 1})
        self.assertEqual(self.model.timer.phase, "break")
        self.assertEqual(self.model.timer.remaining, 300)
        self.assertFalse(self.model.timer.running)
        self.clock.advance(3600)
        self.assertIsNone(self.model.update())
        self.assertEqual(self.model.today_stats["sessions"], 1)

    def test_break_completion_does_not_count_as_focus(self):
        self.model.timer.prepare("break")
        self.model.timer.toggle()
        self.clock.advance(300)
        self.assertEqual(self.model.update(), ("break", 300))
        self.assertEqual(self.model.today_stats["sessions"], 0)
        self.assertEqual(self.model.timer.display, "25:00")
        self.assertFalse(self.model.timer.running)

    def test_selected_duration_and_daily_rollover(self):
        self.model.timer.prepare("focus", 45)
        self.model.timer.toggle()
        self.clock.advance(2700)
        self.model.update()
        self.assertEqual(self.model.today_stats["minutes"], 45)
        self.model.today = lambda: date(2026, 10, 16)
        self.assertEqual(self.model.today_stats["minutes"], 0)
        self.assertEqual(self.model.total_sessions, 1)
        self.assertEqual(self.model.stats["2026-10-15"]["minutes"], 45)

    def test_display_rounds_up_without_negative_seconds(self):
        timer = FocusTimer(remaining=59.1)
        self.assertEqual(timer.display, "01:00")
        timer.remaining = 0
        self.assertEqual(timer.display, "00:00")

    def test_malformed_saved_data_recovers_with_finite_values(self):
        model = Companion(
            {
                "timer": {"focus_minutes": True, "remaining": float("nan"), "phase": []},
                "tasks": "broken",
                "stats": [],
                "preferences": {"scene": {}, "sound": "yes"},
            }
        )
        self.assertEqual(model.timer.display, "25:00")
        self.assertEqual(model.preferences["scene"], "auto")
        self.assertFalse(model.preferences["sound"])
        self.assertEqual(model.tasks, [])

    def test_task_text_is_normalized_limited_and_round_trips(self):
        self.assertFalse(self.model.add_task(" \n "))
        self.assertTrue(self.model.add_task(" 写完一段文章 \n 然后休息 "))
        self.model.tasks[0].done = True
        self.model.add_task("长" * 90)
        restored = Companion(json.loads(json.dumps(self.model.snapshot())))
        self.assertEqual(restored.tasks[0].text, "写完一段文章 然后休息")
        self.assertTrue(restored.tasks[0].done)
        self.assertEqual(len(restored.tasks[1].text), 80)
        self.assertEqual(restored.tasks[0].id, self.model.tasks[0].id)

    def test_reminders_are_periodic_and_can_be_disabled(self):
        self.clock.advance(2699)
        self.assertFalse(self.model.reminder_due())
        self.clock.advance(1)
        self.assertTrue(self.model.reminder_due())
        self.assertFalse(self.model.reminder_due())
        self.model.preferences["reminders"] = False
        self.clock.advance(3000)
        self.assertFalse(self.model.reminder_due())
        self.model.preferences["reminders"] = True
        self.assertFalse(self.model.reminder_due())


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = StateStore(self.temp.name)

    def test_unicode_and_timer_state_survive_a_real_file(self):
        model = Companion()
        model.add_task("读一章书")
        model.timer.remaining = 700.5
        self.assertTrue(self.store.save(model.snapshot()))
        restored = Companion(StateStore(self.temp.name).load())
        self.assertEqual(restored.tasks[0].text, "读一章书")
        self.assertEqual(restored.timer.remaining, 700.5)
        self.assertFalse(restored.timer.running)

    def test_corrupt_file_is_preserved_before_recovery(self):
        self.store.path.write_text("{broken", encoding="utf-8")
        self.assertEqual(self.store.load(), {})
        backups = list(Path(self.temp.name).glob("state.corrupt-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "{broken")
        self.assertTrue(self.store.warning)
        self.assertTrue(self.store.save({"version": 1}))

    def test_failed_atomic_replace_keeps_previous_data_and_cleans_temporary_file(self):
        self.store.save({"original": True})
        with patch("pondpet.storage.os.replace", side_effect=PermissionError):
            self.assertFalse(self.store.save({"replacement": True}))
        self.assertEqual(self.store.load(), {"original": True})
        self.assertEqual(list(Path(self.temp.name).glob(".state-*.tmp")), [])

    def test_unreadable_file_cannot_be_overwritten(self):
        self.store.save({"original": True})
        with patch("pathlib.Path.open", side_effect=PermissionError):
            self.assertEqual(self.store.load(), {})
        self.assertFalse(self.store.save({"replacement": True}))
        self.assertEqual(json.loads(self.store.path.read_text()), {"original": True})


if __name__ == "__main__":
    unittest.main()
