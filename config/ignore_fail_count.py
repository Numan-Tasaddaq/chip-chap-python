# config/ignore_fail_count.py
from dataclasses import dataclass

@dataclass
class IgnoreFailCount:
    package_location: bool = False
    empty_filter_contrast: int = 0
    body_color: bool = False
