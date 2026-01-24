import json
from pathlib import Path
from config.inspection_parameters import InspectionParameters

TEACH_FILE = Path("teach_data.json")


def save_teach_data(params_by_station: dict):
    data = {}
    for station, params in params_by_station.items():
        data[station.value] = params.__dict__

    with open(TEACH_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_teach_data():
    if not TEACH_FILE.exists():
        return {}

    with open(TEACH_FILE, "r") as f:
        raw = json.load(f)

    result = {}
    for station, values in raw.items():
        p = InspectionParameters()
        p.__dict__.update(values)
        result[station] = p

    return result
