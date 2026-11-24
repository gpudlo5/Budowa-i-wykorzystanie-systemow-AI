"""
config.py - wspolna konfiguracja Knowledge Managera (Northway Ltd.).

Importuja ja: ingest.py (buduje baze), search_engine.py (czyta baze),
server.py (Search MCP) oraz Handover MCP. Dzieki temu model, przedrostek
pytania, nazwa kolekcji i sciezki sa zdefiniowane w JEDNYM miejscu.

Nie wymaga zadnych bibliotek spoza standardowej.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------- sciezki

# .../knowledge-manager  (ten plik lezy w servers/common/)
BASE_DIR = Path(__file__).resolve().parents[2]

# Dane zrodlowe (CSV, JSON, documents/*.md); mozna przestawic zmienna KM_DATA_DIR.
DATA_DIR = Path(os.environ.get("KM_DATA_DIR", BASE_DIR / "data"))

# Pliki generowane w trakcie dzialania (w .gitignore).
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = PROCESSED_DIR / "chroma_db"
AUDIT_LOG = PROCESSED_DIR / "audit_log.jsonl"
HANDOVER_DIR = PROCESSED_DIR / "handovers"

# ---------------------------------------------------------------- baza wektorowa

COLLECTION_NAME = "company_documents"

# ---------------------------------------------------------------- model embeddingow

# Mozna podmienic zmienna srodowiskowa KM_EMBEDDING_MODEL, np. na mniejszy
# wariant z rodziny PolDense. Po zmianie modelu TRZEBA przebudowac baze
# (python servers/search/ingest.py), bo wektory z roznych modeli sa niezgodne.
MODEL_NAME = os.environ.get("KM_EMBEDDING_MODEL", "OPI-PIB/PolDense-400M")

# Wg karty modelu: pytania z przedrostkiem, fragmenty dokumentow bez.
# Przy zmianie modelu sprawdz jego karte - inne warianty moga wymagac innego przedrostka.
QUERY_PREFIX = os.environ.get("KM_QUERY_PREFIX", "[query]: ")

# Limit dlugosci tekstu wysylanego do modelu (tokeny). Fragmenty maja ok. 250-300.
MAX_SEQ_LENGTH = 1024

# ---------------------------------------------------------------- uprawnienia

# Awaryjna lista grup, gdy brakuje access_groups.csv.
DEFAULT_GROUPS = [
    "zarzad", "finanse", "hr", "sprzedaz",
    "operacje", "it", "obsluga_klienta",
]

# Zgloszenia i watki sa dostepne dla wszystkich (decyzja z fazy 0).
TICKET_THREAD_ACL = ["all"]

# Prefiks flag uprawnien w metadanych ChromaDB: acl_all, acl_finanse, ...
ACL_PREFIX = "acl_"

# ---------------------------------------------------------------- wyszukiwanie

DEFAULT_TOP_K = 5
MAX_TOP_K = 10


def acl_key(group: str) -> str:
    """Nazwa flagi uprawnien w metadanych, np. 'finanse' -> 'acl_finanse'."""
    return f"{ACL_PREFIX}{group}"
