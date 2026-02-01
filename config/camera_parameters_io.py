from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Optional, Tuple

# Camera parameter keys mapped to old C++ .cam file names
_INT_KEYS = [
    ("Aperture", "shutter_1"),
    ("Aperture2", "shutter_2"),
    ("Gain", "gain"),
    ("Brightness", "brightness"),
    ("BytesPerPkt", "bytes_per_packet"),
    ("BppMin", "bpp_min"),
    ("BppMax", "bpp_max"),
    ("BppInc", "bpp_inc"),
    ("WhiteBalance", "white_balance"),
    ("LCIntensity1", "lc_intensity_1"),
    ("LCIntensity2", "lc_intensity_2"),
    ("LCIntensity3", "lc_intensity_3"),
    ("LCIntensity1Min", "lc_min_1"),
    ("LCIntensity1Max", "lc_max_1"),
    ("LCIntensity2Min", "lc_min_2"),
    ("LCIntensity2Max", "lc_max_2"),
    ("LCIntensity3Min", "lc_min_3"),
    ("LCIntensity3Max", "lc_max_3"),
]

_FLOAT_KEYS = [
    ("RedGain", "red_gain"),
    ("GreenGain", "green_gain"),
    ("BlueGain", "blue_gain"),
]

_DEFAULTS: Dict[str, object] = {
    "shutter_1": 3,
    "shutter_2": 2,
    "gain": 4,
    "brightness": 1,
    "bytes_per_packet": 1072,
    "bpp_min": 80,
    "bpp_max": 8192,
    "bpp_inc": 4,
    "white_balance": 2183066279,
    "lc_intensity_1": 158,
    "lc_intensity_2": 255,
    "lc_intensity_3": 100,
    "lc_min_1": 0,
    "lc_max_1": 255,
    "lc_min_2": 0,
    "lc_max_2": 255,
    "lc_min_3": 0,
    "lc_max_3": 255,
    "red_gain": 1.0,
    "green_gain": 1.0,
    "blue_gain": 1.0,
}


def _cam_file_path(config_dir: Path, config_name: str) -> Path:
    return config_dir / f"{config_name}.cam"


def _parse_rect(value: str) -> Optional[Tuple[int, int, int, int]]:
    try:
        parts = [int(p.strip()) for p in value.split(",")]
        if len(parts) == 4:
            return parts[0], parts[1], parts[2], parts[3]
    except Exception:
        return None
    return None


def _format_rect(rect: Tuple[int, int, int, int]) -> str:
    return f"{rect[0]},{rect[1]},{rect[2]},{rect[3]}"


def load_camera_parameters(
    config_dir: Path,
    config_name: str,
    track_num: int,
) -> Dict[str, object]:
    """
    Load camera parameters from a .cam file.

    - Uses section CamSettingTrack{N} if present, otherwise CamSetting.
    - Returns only keys found in file (does not overwrite defaults).
    """
    cam_path = _cam_file_path(config_dir, config_name)
    if not cam_path.exists():
        return {}

    parser = ConfigParser()
    parser.read(cam_path, encoding="utf-8")

    section_name = f"CamSettingTrack{track_num}"
    if parser.has_section(section_name):
        section = parser[section_name]
    elif parser.has_section("CamSetting"):
        section = parser["CamSetting"]
    else:
        return {}

    loaded: Dict[str, object] = {}

    for cam_key, app_key in _INT_KEYS:
        if cam_key in section:
            try:
                loaded[app_key] = int(section.get(cam_key))
            except ValueError:
                pass

    for cam_key, app_key in _FLOAT_KEYS:
        if cam_key in section:
            try:
                loaded[app_key] = float(section.get(cam_key))
            except ValueError:
                pass

    if "rectAoi" in section:
        rect = _parse_rect(section.get("rectAoi", ""))
        if rect:
            loaded["rect_aoi"] = rect

    if "rectAoiMax" in section:
        rect = _parse_rect(section.get("rectAoiMax", ""))
        if rect:
            loaded["rect_aoi_max"] = rect

    return loaded


def save_camera_parameters(
    config_dir: Path,
    config_name: str,
    track_num: int,
    settings: Dict[str, object],
) -> Path:
    """
    Save camera parameters to a .cam file.

    - Writes to section CamSettingTrack{N}.
    - For track 1, also mirrors to CamSetting for legacy compatibility.
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    cam_path = _cam_file_path(config_dir, config_name)

    parser = ConfigParser()
    if cam_path.exists():
        parser.read(cam_path, encoding="utf-8")

    section_name = f"CamSettingTrack{track_num}"
    if not parser.has_section(section_name):
        parser.add_section(section_name)

    section = parser[section_name]

    def set_value(key: str, value: object) -> None:
        if value is None:
            return
        section[key] = str(value)

    merged = {**_DEFAULTS, **settings}

    for cam_key, app_key in _INT_KEYS:
        set_value(cam_key, int(merged.get(app_key, _DEFAULTS[app_key])))

    for cam_key, app_key in _FLOAT_KEYS:
        set_value(cam_key, float(merged.get(app_key, _DEFAULTS[app_key])))

    if "rect_aoi" in merged and merged["rect_aoi"] is not None:
        rect = merged["rect_aoi"]
        set_value("rectAoi", _format_rect(rect))

    if "rect_aoi_max" in merged and merged["rect_aoi_max"] is not None:
        rect = merged["rect_aoi_max"]
        set_value("rectAoiMax", _format_rect(rect))

    if track_num == 1:
        if not parser.has_section("CamSetting"):
            parser.add_section("CamSetting")
        legacy = parser["CamSetting"]
        for key, value in section.items():
            legacy[key] = value

    with cam_path.open("w", encoding="utf-8") as f:
        parser.write(f)

    return cam_path
