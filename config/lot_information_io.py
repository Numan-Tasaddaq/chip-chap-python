# config/lot_information_io.py
import json
from pathlib import Path
from dataclasses import asdict
from .lot_information import LotInformation

LOT_FILE = Path("lot_information.json")

def save_lot_info(lot_info: LotInformation):
    with LOT_FILE.open("w") as f:
        json.dump(asdict(lot_info), f, indent=4)

def load_lot_info() -> LotInformation:
    if not LOT_FILE.exists():
        return LotInformation()
    
    with LOT_FILE.open("r") as f:
        data = json.load(f)

    # Fill LotInformation dataclass with saved data
    return LotInformation(**data)
