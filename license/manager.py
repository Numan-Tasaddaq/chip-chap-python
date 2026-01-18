from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from config.store import app_data_dir

LICENSE_FILE_NAME = "license.json"
LICENSE_SECRET = "license"


@dataclass
class LicenseData:
    license_key: str
    signature: str  # sha256(license_key + secret)


def license_path() -> Path:
    return app_data_dir() / LICENSE_FILE_NAME


def is_license_present() -> bool:
    return license_path().exists()


def load_license() -> Optional[LicenseData]:
    path = license_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
   

    data.pop("machine_id", None)
    # Check required fields
    if "license_key" not in data or "signature" not in data:
        return None  # or raise a custom error
    


    return LicenseData(**data)


def expected_signature(license_key: str) -> str:
    payload = f"{license_key}|{LICENSE_SECRET}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_license(ld: LicenseData) -> bool:
    return ld.signature == expected_signature(ld.license_key)


def save_license(ld: LicenseData) -> None:
    path = license_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(ld), indent=2), encoding="utf-8")
