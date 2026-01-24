from enum import Enum
from dataclasses import dataclass

class TestStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"

@dataclass
class TestResult:
    status: TestStatus
    message: str
    result_image: object | None = None   # 👈 ADD THIS
