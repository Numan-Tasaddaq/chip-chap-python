# config/lot_information.py
from dataclasses import dataclass, field

@dataclass
class LotInformation:
    machine_id: str = "iTrue #1"
    operator_id: str = ""
    order_no: str = "11111111"
    scan_no: str = ""
    lot_id: str = ""
    lot_size: str = ""
    package_type: str = "Default"
    save_images: dict[str, bool] = field(default_factory=lambda: {
        "pass": False,
        "fail": False,
        "all": False
    })
