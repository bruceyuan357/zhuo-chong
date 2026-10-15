"""Local state with atomic writes and recovery of malformed files."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def default_data_dir():
    if os.environ.get("PONDPET_DATA_DIR"):
        return Path(os.environ["PONDPET_DATA_DIR"]).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PondPet"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "PondPet"
    return Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "pondpet"


class StateStore:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else default_data_dir()
        self.path = self.directory / "state.json"
        self.warning = ""

    def load(self):
        try:
            with self.path.open(encoding="utf-8") as source:
                state = json.load(source)
            if not isinstance(state, dict):
                raise ValueError("Expected an object")
            return state
        except FileNotFoundError:
            return {}
        except (ValueError, UnicodeError):
            backup = self.path.with_name(f"state.corrupt-{datetime.now():%Y%m%d-%H%M%S-%f}.json")
            try:
                shutil.copy2(self.path, backup)
                self.warning = "存档有误，已备份原文件并重新开始。"
            except OSError:
                self.warning = "存档无法读取，也无法备份；本次更改不会覆盖原文件。"
                self._blocked = True
            return {}
        except OSError:
            self.warning = "暂时无法读取存档；本次更改不会覆盖原文件。"
            self._blocked = True
            return {}

    def save(self, state):
        if getattr(self, "_blocked", False):
            return False
        temp_path = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.directory,
                prefix=".state-",
                suffix=".tmp",
                delete=False,
            ) as target:
                temp_path = Path(target.name)
                json.dump(state, target, ensure_ascii=False, indent=2, allow_nan=False)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temp_path, self.path)
            self.warning = ""
            return True
        except (OSError, ValueError, TypeError):
            self.warning = "暂时无法保存。请检查存档目录的写入权限。"
            return False
        finally:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
