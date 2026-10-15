"""Small reusable controls and cached type/icon rendering for the native window."""

from dataclasses import dataclass
from pathlib import Path

import pygame

BG = (246, 246, 239)
INK = (38, 64, 53)
MUTED = (103, 119, 108)
GREEN = (49, 101, 78)
SOFT = (231, 238, 226)
LINE = (222, 228, 217)
WHITE = (255, 255, 251)
ASSETS = Path(__file__).parent / "assets"


@dataclass
class Control:
    key: str
    rect: pygame.Rect
    action: str
    hint: str
    enabled: bool = True


def font_path():
    # SysFont('PingFang SC') silently falls back on some Macs; use the actual CJK font file.
    for path in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ):
        if Path(path).is_file():
            return path
    for name in ("notosanscjksc", "wenquanyimicrohei", "microsoftyahei", "simhei"):
        match = pygame.font.match_font(name)
        if match:
            return match
    return pygame.font.match_font("dejavusans")


class Painter:
    def __init__(self, screen):
        self.screen = screen
        self.font_file = font_path()
        self.number_file = pygame.font.match_font("helveticaneue,arial,dejavusans")
        self.fonts = {}
        self.icons = {}
        self.texts = {}
        self.controls = []
        self.focus = None
        self.keyboard_focus = False
        self.mouse = (0, 0)

    def font(self, size, bold=False, numeric=False):
        key = (size, bold, numeric)
        if key not in self.fonts:
            font = pygame.font.Font(self.number_file if numeric else self.font_file, size)
            font.set_bold(bold)
            self.fonts[key] = font
        return self.fonts[key]

    def text(
        self,
        value,
        pos,
        size=14,
        color=INK,
        bold=False,
        anchor="topleft",
        width=None,
        numeric=False,
    ):
        value = str(value)
        font = self.font(size, bold, numeric)
        if width is not None and font.size(value)[0] > width:
            while value and font.size(value + "…")[0] > width:
                value = value[:-1]
            value += "…"
        key = (value, size, color, bold, numeric)
        if key not in self.texts:
            if len(self.texts) > 400:
                self.texts.clear()
            self.texts[key] = font.render(value, True, color)
        image = self.texts[key]
        rect = image.get_rect(**{anchor: pos})
        self.screen.blit(image, rect)
        return rect

    def box(self, rect, fill=WHITE, radius=12, border=None, thickness=1):
        rect = pygame.Rect(rect)
        if fill is not None:
            pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, rect, thickness, border_radius=radius)
        return rect

    def icon(self, name, center, size=18, color=INK):
        key = (name, size, color)
        if key not in self.icons:
            image = pygame.image.load(str(ASSETS / "icons" / (name + ".png"))).convert_alpha()
            image = pygame.transform.smoothscale(image, (size, size))
            image.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.icons[key] = image
        image = self.icons[key]
        self.screen.blit(image, image.get_rect(center=center))

    def control(self, key, rect, action=None, hint="", enabled=True):
        control = Control(key, pygame.Rect(rect), action or key, hint, enabled)
        self.controls.append(control)
        if key == self.focus and self.keyboard_focus:
            self.box(control.rect.inflate(4, 4), None, 10, GREEN, 2)
        return control

    def button(
        self,
        key,
        rect,
        label="",
        icon=None,
        action=None,
        hint="",
        primary=False,
        selected=False,
        quiet=False,
        enabled=True,
    ):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.mouse) and enabled
        fill = GREEN if primary else SOFT if selected or hover else None if quiet else WHITE
        color = WHITE if primary else INK if enabled else MUTED
        if primary and hover:
            fill = (39, 86, 64)
        self.box(rect, fill, 10, None if quiet or primary or selected else LINE)
        if label and icon:
            text_width = self.font(14).size(label)[0]
            total_width = text_width + 26
            self.icon(icon, (rect.centerx - total_width // 2 + 9, rect.centery), 17, color)
            self.text(
                label,
                (rect.centerx - total_width // 2 + 26, rect.centery),
                14,
                color,
                anchor="midleft",
            )
        elif icon:
            self.icon(icon, rect.center, 17, color)
        elif label:
            self.text(label, rect.center, 13, color, anchor="center")
        return self.control(key, rect, action, hint or label, enabled)

    def begin(self, focus, keyboard_focus):
        self.controls = []
        self.focus = focus
        self.keyboard_focus = keyboard_focus
        self.mouse = pygame.mouse.get_pos()
