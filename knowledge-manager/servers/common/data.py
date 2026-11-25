"""data.py - wspolne wczytywanie plikow z katalogu data/ (CSV i JSON)."""
import csv
import json

from .config import DATA_DIR


def load_csv(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(name: str):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def split_ids(value) -> list[str]:
    """'E002;E003' -> ['E002', 'E003']; lista zostaje lista."""
    if isinstance(value, list):
        return value
    return [v.strip() for v in (value or "").split(";") if v.strip()]