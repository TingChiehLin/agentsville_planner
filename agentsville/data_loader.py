import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_activities():
    with open(DATA_DIR / "activities_db.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_weather():
    with open(DATA_DIR / "weather.json", "r", encoding="utf-8") as f:
        return json.load(f)
