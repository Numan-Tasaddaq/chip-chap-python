# config/store.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict


APP_DIR_NAME = "chipcap"  # change if client wants a different folder name


def app_data_dir() -> Path:
    # Windows: C:\Users\<User>\AppData\Roaming\chipcap
    # Linux/mac: ~/.local/share/chipcap  (depends)
    # We’ll use user home for simplicity and stability.
    base = Path.home() / f".{APP_DIR_NAME}"
    base.mkdir(parents=True, exist_ok=True)
    return base


def config_dir() -> Path:
    d = app_data_dir() / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d


def stations_dir() -> Path:
    d = config_dir() / "stations"
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class Settings:
    pass_image_check_enabled: bool = True
    fail_image_check_enabled: bool = True

    # NEW: ask-once flag
    step3_prompt_shown: bool = False

    startup_online: bool = True
    last_station: str = "Feed"
    step_mode: bool = False



@dataclass
class StationConfig:
    station: str
    enable_package_location: bool = True
    enable_pocket_location: bool = False  # Feed only default per PDF intent


def _read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_first_run_files() -> None:
    """
    Python equivalent of the C++ app auto-creating registry keys/folders on first run.
    """
    # settings.json
    s_path = config_dir() / "settings.json"
    if not s_path.exists():
        _write_json(s_path, asdict(Settings()))

    # per-station configs
    defaults = [
        StationConfig(station="Feed", enable_package_location=True, enable_pocket_location=True),
        StationConfig(station="Top", enable_package_location=True, enable_pocket_location=False),
        StationConfig(station="Bottom", enable_package_location=True, enable_pocket_location=False),
    ]
    for cfg in defaults:
        p = stations_dir() / f"{cfg.station.lower()}.json"
        if not p.exists():
            _write_json(p, asdict(cfg))


def load_settings() -> Settings:
    path = config_dir() / "settings.json"
    raw = _read_json(path) or {}
    return Settings(**{**asdict(Settings()), **raw})


def save_settings(s: Settings) -> None:
    path = config_dir() / "settings.json"
    _write_json(path, asdict(s))
