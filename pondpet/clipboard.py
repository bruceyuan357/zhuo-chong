"""Read text only on an explicit paste command, through the bundled SDL library."""

import ctypes
from functools import lru_cache
from pathlib import Path

import pygame
import pygame.base


@lru_cache(maxsize=1)
def sdl_clipboard():
    candidates = [pygame.base.__file__]
    candidates.extend(str(path) for path in Path(pygame.__file__).parent.glob("*SDL2*.dll"))
    for path in candidates:
        try:
            library = ctypes.CDLL(path)
            library.SDL_GetClipboardText.argtypes = []
            library.SDL_GetClipboardText.restype = ctypes.c_void_p
            library.SDL_free.argtypes = [ctypes.c_void_p]
            library.SDL_free.restype = None
            return library
        except (OSError, AttributeError):
            continue
    return None


def read_text():
    library = sdl_clipboard()
    if library is not None:
        pointer = library.SDL_GetClipboardText()
        if not pointer:
            return ""
        try:
            return ctypes.string_at(pointer).decode("utf-8")
        finally:
            library.SDL_free(pointer)
    if not pygame.scrap.get_init():
        pygame.scrap.init()
    raw = pygame.scrap.get("text/plain;charset=utf-8") or pygame.scrap.get(pygame.SCRAP_TEXT)
    return raw.decode("utf-8").rstrip("\x00") if raw else ""
