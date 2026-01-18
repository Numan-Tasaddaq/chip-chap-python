import json
from pathlib import Path
from dataclasses import asdict
from .inspection_parameters import InspectionParameters  # adjust import path

# File to store parameters
PARAM_FILE = Path("inspection_parameters.json")

def save_parameters(params: InspectionParameters):
    """Save InspectionParameters to JSON file."""
    with PARAM_FILE.open("w") as f:
        json.dump(asdict(params), f, indent=4)

def load_parameters() -> InspectionParameters:
    """Load InspectionParameters from JSON file or return defaults."""
    if not PARAM_FILE.exists():
        return InspectionParameters()
    
    with PARAM_FILE.open("r") as f:
        data = json.load(f)

    # Create model instance from saved data
    return InspectionParameters(**data)
