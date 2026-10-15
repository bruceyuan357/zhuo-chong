"""Timer and task behavior, independent of the display and frame rate."""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional


def number(value, default, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    if not math.isfinite(value):
        return default
    return min(maximum, max(minimum, value))


@dataclass
class FocusTimer:
    focus_minutes: int = 25
    phase: str = "focus"
    duration: float = 1500.0
    remaining: float = 1500.0
    running: bool = False
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    _anchor: Optional[float] = field(default=None, repr=False)

    def tick(self):
        """Return a completed (phase, seconds) once; never auto-start the next phase."""
        if not self.running:
            return None
        now = self.clock()
        elapsed = max(0.0, now - self._anchor) if self._anchor is not None else 0.0
        self._anchor = now
        self.remaining = max(0.0, self.remaining - elapsed)
        if self.remaining > 0:
            return None
        completed = (self.phase, self.duration)
        self.prepare("break" if self.phase == "focus" else "focus")
        return completed

    def toggle(self):
        # The controller ticks before toggling, so a completion is never discarded.
        self.running = not self.running
        self._anchor = self.clock() if self.running else None

    def prepare(self, phase=None, minutes=None):
        if minutes is not None:
            self.focus_minutes = int(number(minutes, 25, 1, 120))
        self.phase = phase if phase in ("focus", "break") else self.phase
        self.duration = float((5 if self.phase == "break" else self.focus_minutes) * 60)
        self.remaining = self.duration
        self.running = False
        self._anchor = None

    @property
    def display(self):
        seconds = math.ceil(self.remaining)
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    @property
    def progress(self):
        return 1.0 - self.remaining / self.duration

    def snapshot(self):
        return {
            "focus_minutes": self.focus_minutes,
            "phase": self.phase,
            "duration": self.duration,
            "remaining": self.remaining,
        }

    @classmethod
    def restore(cls, raw, clock=time.monotonic):
        raw = raw if isinstance(raw, dict) else {}
        minutes = int(number(raw.get("focus_minutes"), 25, 1, 120))
        phase = raw.get("phase") if raw.get("phase") in ("focus", "break") else "focus"
        duration = float((5 if phase == "break" else minutes) * 60)
        remaining = float(number(raw.get("remaining"), duration, 0, duration))
        timer = cls(minutes, phase, duration, remaining, clock=clock)
        if remaining == 0:
            timer.prepare(phase)
        return timer


@dataclass
class Task:
    text: str
    done: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


class Companion:
    def __init__(self, raw=None, clock=time.monotonic, today=date.today):
        raw = raw if isinstance(raw, dict) else {}
        self.clock, self.today = clock, today
        self.timer = FocusTimer.restore(raw.get("timer"), clock)
        self.tasks = []
        task_rows = raw.get("tasks", [])
        for row in task_rows[:50] if isinstance(task_rows, list) else []:
            if isinstance(row, dict) and isinstance(row.get("text"), str) and row["text"].strip():
                task_id = row.get("id")
                self.tasks.append(
                    Task(
                        row["text"].strip()[:80],
                        row.get("done") is True,
                        task_id if isinstance(task_id, str) else uuid.uuid4().hex,
                    )
                )
        self.stats = {}
        stats = raw.get("stats", {})
        for day, values in stats.items() if isinstance(stats, dict) else []:
            try:
                date.fromisoformat(day)
            except (ValueError, TypeError):
                continue
            if isinstance(values, dict):
                self.stats[day] = {
                    "minutes": int(number(values.get("minutes"), 0, 0, 1440)),
                    "sessions": int(number(values.get("sessions"), 0, 0, 1440)),
                }
        prefs = raw.get("preferences", {})
        prefs = prefs if isinstance(prefs, dict) else {}
        self.preferences = {
            "scene": prefs.get("scene")
            if prefs.get("scene") in ("auto", "day", "night")
            else "auto",
            "rain": prefs.get("rain") is True,
            "reduced_motion": prefs.get("reduced_motion") is True,
            "sound": prefs.get("sound") is True,
            "reminders": prefs.get("reminders", True) is True,
            "compact": prefs.get("compact") is True,
        }
        self.last_reminder = clock()

    @property
    def today_stats(self):
        return self.stats.get(self.today().isoformat(), {"minutes": 0, "sessions": 0})

    @property
    def total_sessions(self):
        return sum(day["sessions"] for day in self.stats.values())

    def update(self):
        completed = self.timer.tick()
        if completed and completed[0] == "focus":
            key = self.today().isoformat()
            stats = self.stats.setdefault(key, {"minutes": 0, "sessions": 0})
            stats["minutes"] += int(completed[1] // 60)
            stats["sessions"] += 1
        return completed

    def add_task(self, text):
        text = " ".join(text.split())[:80]
        if not text or len(self.tasks) >= 50:
            return False
        self.tasks.append(Task(text))
        return True

    def reminder_due(self):
        now = self.clock()
        if not self.preferences["reminders"]:
            self.last_reminder = now
            return False
        if now - self.last_reminder >= 45 * 60:
            self.last_reminder = now
            return True
        return False

    def snapshot(self):
        return {
            "version": 1,
            "timer": self.timer.snapshot(),
            "tasks": [vars(task).copy() for task in self.tasks],
            "stats": self.stats,
            "preferences": self.preferences.copy(),
        }
