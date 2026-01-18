# config/auto_run_setting.py
from dataclasses import dataclass

@dataclass
class AutoRunSetting:
    delay_time: int = 100  # default delay
