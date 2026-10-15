"""Native pond companion. All personal data stays in a local JSON file."""

from __future__ import annotations

import argparse
import math
import os
import time
from array import array
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
from pygame._sdl2.video import Window

from .clipboard import read_text
from .model import Companion
from .scene import Garden
from .storage import StateStore
from .ui import BG, GREEN, INK, LINE, MUTED, SOFT, WHITE, Painter

FULL_SIZE = (448, 752)
COMPACT_SIZE = (320, 286)


class DesktopPet:
    def __init__(self, data_dir=None, compact=None):
        pygame.display.init()
        pygame.font.init()
        self.store = StateStore(data_dir)
        self.model = Companion(self.store.load())
        if compact is not None:
            self.model.preferences["compact"] = compact
        self.desktop = pygame.display.get_desktop_sizes()[0]
        size = COMPACT_SIZE if self.compact else FULL_SIZE
        self.screen = pygame.display.set_mode(size, pygame.NOFRAME)
        pygame.display.set_caption("栖水 · 水潭桌宠")
        self.window = Window.from_display_module()
        self.window.position = (
            max(0, self.desktop[0] - size[0] - 60),
            max(30, min(100, self.desktop[1] - size[1] - 40)),
        )
        self.ui = Painter(self.screen)
        self.garden = Garden()
        icon = pygame.image.load(str(Path(__file__).parent / "assets/icons/leaf.png"))
        pygame.display.set_icon(icon)
        self.running = True
        self.minimized = False
        self.panel = None
        self.focus = None
        self.keyboard_focus = False
        self.input_active = False
        self.draft = ""
        self.composition = ""
        self.ignore_shortcut_text_until = 0.0
        self.scroll = 0
        self.drag_anchor = None
        self.notice = ""
        self.notice_until = 0.0
        self.last_save = time.monotonic()
        self.closed = False
        self._chime = None
        if self.store.warning:
            self.toast(self.store.warning, 15)
        self.render()

    @property
    def compact(self):
        return self.model.preferences["compact"]

    @property
    def scene_rect(self):
        return pygame.Rect(12, 48, 296, 176) if self.compact else pygame.Rect(24, 84, 400, 240)

    def toast(self, message, duration=7):
        self.notice, self.notice_until = message, time.monotonic() + duration

    def save(self):
        self.last_save = time.monotonic()
        saved = self.store.save(self.model.snapshot())
        if not saved:
            self.toast(self.store.warning, 15)
        return saved

    def chime(self):
        if not self.model.preferences["sound"]:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            if self._chime is None:
                samples = array(
                    "h",
                    [
                        int(2600 * math.sin(2 * math.pi * 660 * i / 22050) * math.exp(-i / 4000))
                        for i in range(12000)
                    ],
                )
                self._chime = pygame.mixer.Sound(buffer=samples)
            self._chime.play()
        except pygame.error:
            self.model.preferences["sound"] = False
            self.toast("声音暂不可用，仍会显示文字提醒。")
            self.save()

    def advance_timer(self):
        completed = self.model.update()
        if completed:
            self.chime()
            self.toast(
                "专注完成。喝口水，让眼睛休息 5 分钟吧。"
                if completed[0] == "focus"
                else "休息结束，准备好再开始下一段专注。",
                90,
            )
            self.save()
        return completed

    def update(self, dt):
        self.advance_timer()
        self.garden.update(dt, self.model.preferences)
        if self.model.reminder_due():
            self.toast("陪伴已满 45 分钟。喝口水，看看远处吧。", 90)
            self.chime()
        if time.monotonic() - self.last_save >= 15 and self.model.timer.running:
            self.save()

    def edit_input(self, active):
        self.input_active = active
        self.composition = ""
        if active:
            self.focus = "task-input"
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(pygame.Rect(40, 560, 336, 42))
        else:
            pygame.key.stop_text_input()

    def add_task(self):
        if self.model.add_task(self.draft):
            self.draft = ""
            self.scroll = max(0, len(self.model.tasks) - 2)
            self.save()
            self.toast("记下了。一次做好一件小事。")
        elif not self.draft.strip():
            self.toast("先写下一件想做的小事。")
        else:
            self.toast("已经记下 50 件小事，先整理一下吧。")

    def resize(self):
        position = self.window.position
        size = COMPACT_SIZE if self.compact else FULL_SIZE
        self.screen = pygame.display.set_mode(size, pygame.NOFRAME)
        self.window = Window.from_display_module()
        self.window.position = (
            max(0, min(position[0], self.desktop[0] - size[0])),
            max(25, min(position[1], self.desktop[1] - size[1] - 25)),
        )
        self.ui.screen = self.screen
        self.edit_input(False)
        self.panel = None
        self.focus = None
        self.drag_anchor = None

    def action(self, action):
        timer = self.model.timer
        self.advance_timer()
        if action == "close":
            self.running = False
        elif action == "minimize":
            self.window.minimize()
        elif action == "compact":
            self.model.preferences["compact"] = not self.compact
            self.resize()
            self.save()
        elif action in ("settings", "help"):
            if self.compact:
                self.model.preferences["compact"] = False
                self.resize()
            self.panel = action
            self.edit_input(False)
            self.focus = "panel-close"
        elif action == "panel-close":
            self.panel = None
            self.focus = None
        elif action == "task-input":
            self.edit_input(True)
        elif action == "task-add":
            self.add_task()
        elif action == "timer":
            timer.toggle()
            self.save()
        elif action == "reset":
            if timer.running:
                self.toast("先暂停，再重新开始这一段。")
            else:
                timer.prepare()
                self.save()
        elif action.startswith("phase:") or action.startswith("duration:"):
            if timer.running:
                self.toast("先暂停，再切换专注或休息时长。")
            else:
                if action.startswith("phase:"):
                    timer.prepare(action.split(":")[1])
                else:
                    timer.prepare("focus", int(action.split(":")[1]))
                self.save()
        elif action == "rain":
            self.model.preferences["rain"] = not self.model.preferences["rain"]
            if self.model.preferences["reduced_motion"]:
                self.toast("已保存天气偏好；关闭「减少动态」后可见细雨。")
            self.save()
        elif action.startswith("scene:"):
            self.model.preferences["scene"] = action.split(":")[1]
            self.save()
        elif action.startswith("toggle:"):
            key = action.split(":")[1]
            self.model.preferences[key] = not self.model.preferences[key]
            if key == "sound" and self.model.preferences[key]:
                self.chime()
            self.save()
        elif action.startswith("task:"):
            task_id = action.split(":")[1]
            for task in self.model.tasks:
                if task.id == task_id:
                    task.done = not task.done
                    if task.done:
                        self.toast("又完成了一件小事。慢慢来，也很好。")
                        self.garden.splash(big=True)
                    self.save()
                    break
        elif action.startswith("delete:"):
            task_id = action.split(":")[1]
            self.model.tasks = [task for task in self.model.tasks if task.id != task_id]
            self.scroll = min(self.scroll, max(0, len(self.model.tasks) - 2))
            self.save()

    def tab_focus(self, backwards=False):
        controls = [control for control in self.ui.controls if control.enabled]
        if not controls:
            return
        keys = [control.key for control in controls]
        index = keys.index(self.focus) if self.focus in keys else (0 if backwards else -1)
        self.focus = keys[(index + (-1 if backwards else 1)) % len(keys)]
        self.keyboard_focus = True
        self.edit_input(self.focus == "task-input")

    def handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.panel:
                self.action("panel-close")
            elif self.input_active:
                self.edit_input(False)
                self.focus = None
            else:
                self.running = False
            return
        if event.key == pygame.K_TAB:
            self.tab_focus(bool(event.mod & pygame.KMOD_SHIFT))
            return
        if self.input_active:
            if event.key == pygame.K_BACKSPACE and not self.composition:
                self.draft = self.draft[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and not self.composition:
                self.add_task()
            elif event.key == pygame.K_v and event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META):
                try:
                    pasted = read_text()
                    if pasted:
                        self.draft = (self.draft + " ".join(pasted.split()))[:80]
                except (pygame.error, UnicodeError, NotImplementedError):
                    self.toast("此系统暂不支持粘贴，请直接输入。")
            return
        if (
            event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
            and self.keyboard_focus
        ):
            for control in self.ui.controls:
                if control.key == self.focus and control.enabled:
                    self.action(control.action)
                    return
        if self.panel:
            return
        if event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) and not self.compact:
            direction = -2 if event.key == pygame.K_PAGEUP else 2
            self.scroll = max(0, min(max(0, len(self.model.tasks) - 2), self.scroll + direction))
            self.focus = None
            return
        shortcuts = {
            pygame.K_SPACE: "timer",
            pygame.K_c: "compact",
            pygame.K_r: "rain",
            pygame.K_h: "help",
            pygame.K_F1: "help",
            pygame.K_n: "task-input",
        }
        if event.key == pygame.K_n and self.compact:
            self.action("compact")
        if event.key == pygame.K_n:
            self.ignore_shortcut_text_until = time.monotonic() + 0.25
        if event.key in shortcuts:
            self.action(shortcuts[event.key])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event)
            elif event.type == pygame.TEXTINPUT and self.input_active:
                if event.text.lower() == "n" and time.monotonic() < self.ignore_shortcut_text_until:
                    self.ignore_shortcut_text_until = 0.0
                    continue
                self.draft = (self.draft + event.text)[:80]
                self.composition = ""
            elif event.type == pygame.TEXTEDITING and self.input_active:
                self.composition = event.text
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.drag_anchor = None
                self.save()
            elif event.type == pygame.WINDOWMINIMIZED:
                self.minimized = True
            elif event.type == pygame.WINDOWRESTORED:
                self.minimized = False
            elif event.type == pygame.MOUSEWHEEL and not self.panel and not self.compact:
                self.scroll = max(0, min(max(0, len(self.model.tasks) - 2), self.scroll - event.y))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.keyboard_focus = False
                if event.button not in (1, 3):
                    continue
                control = next(
                    (
                        control
                        for control in reversed(self.ui.controls)
                        if control.rect.collidepoint(event.pos)
                    ),
                    None,
                )
                if control:
                    if event.button == 1 and control.enabled:
                        self.focus = control.key
                        if control.key not in ("task-input", "task-add"):
                            self.edit_input(False)
                        self.action(control.action)
                elif self.panel:
                    continue
                elif event.button == 1 and event.pos[1] < (44 if self.compact else 56):
                    self.drag_anchor = event.pos
                    self.edit_input(False)
                elif self.scene_rect.collidepoint(event.pos):
                    self.edit_input(False)
                    x = (event.pos[0] - self.scene_rect.x) / self.scene_rect.w
                    y = (event.pos[1] - self.scene_rect.y) / self.scene_rect.h
                    if self.model.preferences["reduced_motion"]:
                        self.toast("水潭正在安静陪伴；可在设置中开启动态。")
                    elif event.button == 1:
                        self.garden.feed(x, y)
                    else:
                        self.garden.splash(x, y, True)
                else:
                    self.edit_input(False)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.drag_anchor = None
            elif event.type == pygame.MOUSEMOTION and self.drag_anchor:
                x, y = self.window.position
                self.window.position = (
                    x + event.pos[0] - self.drag_anchor[0],
                    y + event.pos[1] - self.drag_anchor[1],
                )

    def header(self):
        ui = self.ui
        if self.compact:
            ui.icon("leaf", (25, 23), 17, GREEN)
            ui.text("栖水", (42, 14), 17, bold=True)
            ui.text("POND", (86, 21), 9, MUTED, numeric=True)
            ui.button("compact", (218, 9, 28, 28), icon="maximize-2", quiet=True, hint="展开 · C")
            ui.button("minimize", (250, 9, 28, 28), icon="minus", quiet=True, hint="最小化")
            ui.button("close", (282, 9, 28, 28), icon="x", quiet=True, hint="保存并退出 · Esc")
            return
        ui.box((24, 14, 32, 32), SOFT, 11)
        ui.icon("leaf", (40, 30), 20, GREEN)
        ui.text("栖水", (66, 10), 24, bold=True)
        ui.text("P O N D  C O M P A N I O N", (68, 39), 8, MUTED, numeric=True)
        for key, x, icon, hint in [
            ("help", 278, "circle-help", "操作指南 · H"),
            ("settings", 308, "settings-2", "陪伴设置"),
            ("compact", 338, "minimize-2", "迷你陪伴 · C"),
            ("minimize", 368, "minus", "最小化"),
            ("close", 398, "x", "保存并退出 · Esc"),
        ]:
            ui.button(key, (x, 15, 28, 28), icon=icon, quiet=True, hint=hint)
        ui.text("留一点宁静，也做一点小事。", (24, 63), 13, MUTED)
        ui.text(
            datetime.now().strftime("%H:%M"), (424, 63), 12, MUTED, anchor="topright", numeric=True
        )

    def draw_garden(self):
        ui, prefs = self.ui, self.model.preferences
        rect = self.scene_rect
        golden = self.model.total_sessions >= 3
        self.garden.draw(self.screen, rect, prefs, golden)
        period = self.garden.period(prefs)
        label = "夜色" if period == "night" else "晨昏" if period == "golden" else "日间"
        label += " · 细雨" if prefs["rain"] else " · 微风"
        badge = (rect.x + 12, rect.y + 12, 112, 28)
        ui.box(badge, BG, 14)
        ui.icon("moon" if period == "night" else "sun", (rect.x + 28, rect.y + 26), 14, GREEN)
        ui.text(label, (rect.x + 42, rect.y + 26), 11, INK, anchor="midleft")
        ui.button(
            "rain",
            (rect.right - 40, rect.y + 12, 28, 28),
            icon="cloud-rain",
            selected=prefs["rain"],
            hint="切换细雨 · R",
        )
        if not self.compact:
            ui.box((rect.x + 12, rect.bottom - 34, 166, 24), BG, 12)
            ui.text(
                "金色时刻 · 谢谢你的专注" if golden else "点击水面，喂一口鱼",
                (rect.x + 24, rect.bottom - 22),
                11,
                INK,
                anchor="midleft",
            )
        if self.notice and time.monotonic() < self.notice_until:
            ui.box((rect.x + 8, rect.bottom - 38, rect.w - 16, 30), BG, 10)
            ui.text(
                self.notice,
                (rect.x + 18, rect.bottom - 23),
                11,
                INK,
                width=rect.w - 36,
                anchor="midleft",
            )

    def timer_card(self):
        ui, timer = self.ui, self.model.timer
        if self.compact:
            ui.text(timer.display, (20, 235), 29, numeric=True)
            ui.text("休息" if timer.phase == "break" else "专注", (106, 246), 12, MUTED)
            ui.button(
                "timer",
                (180, 236, 126, 36),
                "暂停" if timer.running else "开始休息" if timer.phase == "break" else "开始专注",
                "pause" if timer.running else "play",
                primary=True,
                hint="开始或暂停 · 空格",
            )
            return
        ui.box((24, 340, 400, 172), WHITE, 16, LINE)
        ui.button(
            "phase-focus",
            (40, 353, 56, 26),
            "专注",
            action="phase:focus",
            selected=timer.phase == "focus",
            quiet=True,
        )
        ui.button(
            "phase-break",
            (100, 353, 56, 26),
            "休息",
            action="phase:break",
            selected=timer.phase == "break",
            quiet=True,
        )
        stats = self.model.today_stats
        ui.text(
            f"今日 {stats['minutes']} 分钟 · {stats['sessions']} 次",
            (406, 366),
            11,
            MUTED,
            anchor="midright",
        )
        ui.text(timer.display, (40, 387), 51, INK, numeric=True)
        label = (
            "暂停"
            if timer.running
            else "开始休息"
            if timer.phase == "break"
            else "继续专注"
            if timer.progress
            else "开始专注"
        )
        ui.button(
            "timer",
            (252, 399, 156, 44),
            label,
            "pause" if timer.running else "play",
            primary=True,
            hint="开始或暂停 · 空格",
        )
        status = (
            "让眼睛看看远处。"
            if timer.phase == "break"
            else "水流慢慢，小事一件一件。"
            if timer.running
            else "准备好，就从此刻开始。"
        )
        ui.text(status, (42, 446), 11, MUTED)
        ui.box((42, 466, 364, 3), SOFT, 1)
        if timer.progress:
            ui.box((42, 466, max(2, int(364 * timer.progress)), 3), GREEN, 1)
        if timer.phase == "focus":
            for minutes, x in [(25, 40), (45, 106), (60, 172)]:
                ui.button(
                    f"duration-{minutes}",
                    (x, 478, 58, 25),
                    f"{minutes} 分",
                    action=f"duration:{minutes}",
                    selected=timer.focus_minutes == minutes,
                    quiet=True,
                    hint=f"专注 {minutes} 分钟",
                )
        else:
            ui.text("5 分钟休息，不必急着回来。", (42, 484), 11, MUTED)
        ui.button(
            "reset", (376, 476, 32, 28), icon="rotate-ccw", quiet=True, hint="重新计时（先暂停）"
        )

    def task_list(self):
        ui = self.ui
        tasks = self.model.tasks
        ui.text("随手记", (24, 533), 17, bold=True)
        done = sum(task.done for task in tasks)
        ui.text(f"{done} / {len(tasks)} 完成", (424, 539), 11, MUTED, anchor="midright")
        ui.box((24, 560, 400, 42), WHITE, 11, GREEN if self.input_active else LINE)
        ui.control("task-input", (28, 562, 346, 38), hint="输入一件小事 · N")
        text = self.draft + self.composition
        font = ui.font(14)
        # Keep the caret and IME composition visible when an 80-character note exceeds the field.
        visible = text
        while font.size(visible)[0] > 318:
            visible = visible[1:]
        if text:
            ui.text(visible, (40, 581), 14, INK, anchor="midleft")
        else:
            ui.text("写下一件想做的小事…", (40, 581), 13, MUTED, anchor="midleft")
        if self.input_active and int(time.monotonic() * 2) % 2 == 0:
            x = min(360, 40 + font.size(visible)[0] + 2)
            pygame.draw.line(self.screen, GREEN, (x, 572), (x, 590), 1)
        ui.button(
            "task-add", (382, 566, 32, 30), icon="plus", selected=True, hint="记下这件事 · Enter"
        )
        if not tasks:
            ui.text("想做什么，先记下一件。", (224, 641), 14, MUTED, anchor="center")
            ui.text("完成它，再慢慢开始下一件。", (224, 667), 11, MUTED, anchor="center")
            return
        self.scroll = min(self.scroll, max(0, len(tasks) - 2))
        for row, task in enumerate(tasks[self.scroll : self.scroll + 2]):
            y = 610 + row * 44
            key = f"task:{task.id}"
            ui.button(key, (26, y, 356, 40), quiet=True, hint="完成或恢复这件小事")
            ui.box(
                (38, y + 11, 18, 18), GREEN if task.done else WHITE, 6, None if task.done else LINE
            )
            if task.done:
                ui.icon("check", (47, y + 20), 13, WHITE)
            text_rect = ui.text(
                task.text,
                (68, y + 20),
                13,
                MUTED if task.done else INK,
                anchor="midleft",
                width=300,
            )
            if task.done:
                pygame.draw.line(self.screen, MUTED, text_rect.midleft, text_rect.midright, 1)
            ui.button(
                f"delete:{task.id}", (392, y + 6, 28, 28), icon="x", quiet=True, hint="移除这件小事"
            )
        if len(tasks) > 2:
            ui.text(
                f"滚动查看 · {self.scroll + 1}–{min(self.scroll + 2, len(tasks))} / {len(tasks)}",
                (424, 711),
                10,
                MUTED,
                anchor="topright",
            )

    def panel_content(self):
        ui, prefs = self.ui, self.model.preferences
        veil = pygame.Surface(FULL_SIZE, pygame.SRCALPHA)
        veil.fill((31, 52, 42, 100))
        self.screen.blit(veil, (0, 0))
        # Only visible modal controls enter the tab/click order.
        ui.controls = []
        ui.box((24, 112, 400, 516), BG, 20)
        ui.text("陪伴设置" if self.panel == "settings" else "慢慢上手", (44, 140), 21, bold=True)
        ui.button("panel-close", (374, 132, 30, 30), icon="x", quiet=True, hint="返回 · Esc")
        if self.panel == "help":
            lines = [
                ("点击水面", "喂鱼；右键轻点，漾起水花。"),
                ("空格", "开始或暂停专注与休息。"),
                ("N / Enter", "记下一件小事；回车保存。"),
                ("R / C", "切换细雨 / 展开或收起迷你陪伴。"),
                ("Tab / Shift + Tab", "移动焦点；回车操作；Esc 返回或退出。"),
                ("拖动顶部", "把水潭放在你喜欢的位置。"),
            ]
            for row, (title, body) in enumerate(lines):
                y = 192 + row * 55
                ui.text(title, (44, y), 13, bold=True)
                ui.text(body, (44, y + 23), 11, MUTED)
            ui.text("专注结束后，手动开始 5 分钟休息。", (44, 540), 12, MUTED)
            ui.text("退出会保留剩余时间；重开时保持暂停。", (44, 564), 12, MUTED)
            ui.text("完成 3 段专注，解锁水潭的金色时刻。", (44, 588), 12, MUTED)
            return
        ui.text("水潭光景", (44, 193), 14, bold=True)
        ui.text("自动模式跟随本机时间，天气为氛围效果。", (44, 219), 11, MUTED)
        for key, label, x in [
            ("auto", "跟随时间", 44),
            ("day", "日间", 164),
            ("night", "夜色", 284),
        ]:
            ui.button(
                "scene-" + key,
                (x, 246, 108, 34),
                label,
                action="scene:" + key,
                selected=prefs["scene"] == key,
            )
        rows = [
            ("rain", "细雨", "让水面多一点涟漪。", "rain"),
            ("reduced_motion", "减少动态", "停下游鱼、水花、细雨和萤光。", "toggle:reduced_motion"),
            ("sound", "轻声提醒", "专注结束与休息结束时，响一声。", "toggle:sound"),
            ("reminders", "喝水与远眺", "运行满 45 分钟，在水潭内轻轻提醒。", "toggle:reminders"),
        ]
        for row, (key, title, subtitle, action) in enumerate(rows):
            y = 305 + row * 62
            ui.text(title, (44, y), 14)
            ui.text(subtitle, (44, y + 24), 11, MUTED)
            ui.button(
                "pref-" + key,
                (350, y + 2, 44, 28),
                "开" if prefs[key] else "关",
                selected=prefs[key],
                action=action,
                hint=f"切换{title}",
            )
        ui.text("无需账号或联网。待办、偏好和专注记录仅存本机。", (44, 578), 11, MUTED)
        ui.text("提醒仅在应用运行时生效。", (44, 601), 10, MUTED)

    def render(self):
        self.ui.begin(self.focus, self.keyboard_focus)
        self.screen.fill(BG)
        self.header()
        self.draw_garden()
        self.timer_card()
        if not self.compact:
            self.task_list()
            pygame.draw.line(self.screen, LINE, (24, 721), (424, 721))
            self.ui.icon("leaf", (31, 736), 13, GREEN)
            self.ui.text(
                "存档暂不可用" if self.store.warning else "仅在本机保存",
                (43, 736),
                10,
                (156, 76, 56) if self.store.warning else MUTED,
                anchor="midleft",
            )
            self.ui.text("空格 专注   R 细雨   C 迷你", (424, 736), 10, MUTED, anchor="midright")
        if self.panel:
            self.panel_content()
        # Hover labels expose icon-only controls without covering their targets.
        hovered = next(
            (
                control
                for control in reversed(self.ui.controls)
                if control.rect.collidepoint(self.ui.mouse) and control.hint
            ),
            None,
        )
        if hovered and not self.input_active:
            hint = hovered.hint
            w = self.ui.font(11).size(hint)[0] + 20
            x = max(8, min(hovered.rect.centerx - w // 2, self.screen.get_width() - w - 8))
            y = min(hovered.rect.bottom + 6, self.screen.get_height() - 32)
            self.ui.box((x, y, w, 25), BG, 8, LINE)
            self.ui.text(hint, (x + 10, y + 12), 11, INK, anchor="midleft")
        pygame.display.flip()

    def close(self):
        if self.closed:
            return
        self.advance_timer()
        self.save()
        self.closed = True
        pygame.quit()

    def run(self, frames=None, screenshot=None):
        clock = pygame.time.Clock()
        count = 0
        try:
            while self.running and (frames is None or count < frames):
                fps = (
                    10 if self.minimized else 15 if self.model.preferences["reduced_motion"] else 30
                )
                dt = clock.tick(fps) / 1000.0
                self.handle_events()
                self.update(dt)
                if not self.minimized:
                    self.render()
                count += 1
            if screenshot:
                pygame.image.save(self.screen, str(screenshot))
        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description="栖水 · 离线水潭桌宠与专注陪伴")
    parser.add_argument("--data-dir", type=Path, help="本地存档目录")
    parser.add_argument("--compact", action="store_true", default=None, help="以迷你模式启动")
    parser.add_argument("--frames", type=int, help="渲染指定帧数后退出（用于显示环境检查）")
    parser.add_argument("--screenshot", type=Path, help="退出时保存画面")
    args = parser.parse_args()
    DesktopPet(args.data_dir, args.compact).run(args.frames, args.screenshot)


if __name__ == "__main__":
    main()
